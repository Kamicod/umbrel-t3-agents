"""hs-embed-1 (int8 ONNX) as a tiny OpenAI-compatible embeddings server.

POST /v1/embeddings {"input": str | [str], "model": "..."} -> {"data": [{"embedding": [...], "index": i}], ...}
GET  /health

Same file runs on the Mac (distillation) and on the Pi (Umbrel app), so both produce identical
vectors. Mean pooling over the attention mask (hs-embed-1's sentence-transformers config), then
L2-normalized (cosine similarity is unchanged by normalization).

Env: EMBED_MODEL_DIR (model_int8.onnx + tokenizer.json), EMBED_PORT (8181), EMBED_HOST (0.0.0.0),
     EMBED_API_KEY (optional bearer key), EMBED_MAX_TOKENS (2048), EMBED_THREADS (cores),
     EMBED_BATCH (32 texts per ONNX run).
"""
import base64
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

MODEL_DIR = os.environ.get("EMBED_MODEL_DIR", os.path.join(os.path.dirname(__file__), "model"))
PORT = int(os.environ.get("EMBED_PORT", "8181"))
HOST = os.environ.get("EMBED_HOST", "0.0.0.0")
API_KEY = os.environ.get("EMBED_API_KEY", "")
MAX_TOKENS = int(os.environ.get("EMBED_MAX_TOKENS", "2048"))
BATCH = int(os.environ.get("EMBED_BATCH", "32"))
MODEL_NAME = "hs-embed-1-int8"

opts = ort.SessionOptions()
opts.intra_op_num_threads = int(os.environ.get("EMBED_THREADS", "0"))  # 0 = all cores
opts.enable_cpu_mem_arena = False  # keeps RSS from growing with the largest batch seen
session = ort.InferenceSession(os.path.join(MODEL_DIR, "model_int8.onnx"), opts, providers=["CPUExecutionProvider"])
tokenizer = Tokenizer.from_file(os.path.join(MODEL_DIR, "tokenizer.json"))
tokenizer.enable_truncation(MAX_TOKENS)
pad_id = tokenizer.token_to_id("<pad>") or tokenizer.token_to_id("[PAD]") or 0
tokenizer.enable_padding(pad_id=pad_id)
lock = threading.Lock()  # one ONNX run at a time; it already uses every core


def trim_heap():
    """Give freed heap back to the OS (Linux/glibc). Loading the 256k-token tokenizer.json
    parses ~34 MB of JSON and leaves ~400 MB of freed-but-retained heap behind."""
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass  # not glibc (macOS): nothing to do


trim_heap()


def embed(texts):
    out = []
    # Sort by length so each batch pads as little as possible, then restore order.
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    for start in range(0, len(order), BATCH):
        idx = order[start:start + BATCH]
        encs = tokenizer.encode_batch([texts[i] for i in idx])
        ids = np.array([e.ids for e in encs], dtype=np.int64)
        mask = np.array([e.attention_mask for e in encs], dtype=np.int64)
        with lock:
            hidden = session.run(None, {"input_ids": ids, "attention_mask": mask})[0]
        m = mask[..., None].astype(np.float32)
        vec = (hidden * m).sum(1) / np.clip(m.sum(1), 1e-9, None)
        vec /= np.clip(np.linalg.norm(vec, axis=1, keepdims=True), 1e-12, None)
        out.extend(zip(idx, vec, (len(e.ids) for e in encs)))
    out.sort(key=lambda t: t[0])
    return [v for _, v, _ in out], sum(n for _, _, n in out)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):
        if self.path.rstrip("/") == "/health":
            return self._send(200, {"ok": True, "model": MODEL_NAME, "dimensions": 384})
        if self.path.rstrip("/") == "/v1/models":
            return self._send(200, {"object": "list", "data": [{"id": MODEL_NAME, "object": "model"}]})
        self._send(404, {"error": {"message": "not found"}})

    def do_POST(self):
        if self.path.rstrip("/") != "/v1/embeddings":
            return self._send(404, {"error": {"message": "not found"}})
        if API_KEY and self.headers.get("authorization", "") != f"Bearer {API_KEY}":
            return self._send(401, {"error": {"message": "invalid API key"}})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
            inp = body.get("input")
            texts = [inp] if isinstance(inp, str) else list(inp or [])
            if not texts or not all(isinstance(t, str) for t in texts):
                return self._send(400, {"error": {"message": "input must be a string or list of strings"}})
            vecs, n_tokens = embed(texts)
            as_b64 = body.get("encoding_format") == "base64"  # the OpenAI SDK asks for this by default
            enc = (lambda v: base64.b64encode(v.astype("<f4").tobytes()).decode()) if as_b64 else (lambda v: v.tolist())
            self._send(200, {
                "object": "list", "model": MODEL_NAME,
                "data": [{"object": "embedding", "index": i, "embedding": enc(v)} for i, v in enumerate(vecs)],
                "usage": {"prompt_tokens": n_tokens, "total_tokens": n_tokens},
            })
        except Exception as e:  # never crash the server on one bad request
            self._send(500, {"error": {"message": str(e)}})
        finally:
            trim_heap()


if __name__ == "__main__":
    print(f"hs-embed-1 int8 listening on {HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
