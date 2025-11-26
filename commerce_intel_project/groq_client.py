# groq_client.py
import os, json
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = 'llama-3.1-8b-instant'

# Try import Groq; if not available, disable
try:
    from groq import Groq
except Exception:
    Groq = None

class GroqClient:
    def __init__(self):
        self._configured = False
        self.client = None
        if GROQ_API_KEY and Groq is not None:
            try:
                self.client = Groq(api_key=GROQ_API_KEY)
                self._configured = True
            except Exception:
                self._configured = False

    def is_configured(self):
        return self._configured

    def summarize(self, context_json):
        if not self._configured:
            return self._fallback_summary(context_json)
        prompt = (
            "You are an AI sales analyst. Given this JSON context, produce a short executive summary (3-4 sentences),"
            " five high-impact findings, and five actionable recommendations. Context:\n" + json.dumps(context_json, default=str)
        )
        try:
            resp = self.client.generate(model=GROQ_MODEL, input=prompt, max_output_tokens=512)
            if isinstance(resp, dict):
                return resp.get('output') or resp.get('text') or str(resp)
            return str(resp)
        except Exception as e:
            return f"Groq error: {e}"

    def answer_question(self, context_json, question):
        if not self._configured:
            return "Groq not configured. Cannot answer."
        prompt = (
            "You are an AI analyst. Use only the provided JSON context to answer the question. If insufficient data, say so.\n"
            f"Context: {json.dumps(context_json, default=str)}\nQuestion: {question}"
        )
        try:
            resp = self.client.generate(model=GROQ_MODEL, input=prompt, max_output_tokens=512)
            if isinstance(resp, dict):
                return resp.get('output') or resp.get('text') or str(resp)
            return str(resp)
        except Exception as e:
            return f"Groq error: {e}"

    def _fallback_summary(self, context_json):
        lines = []
        lines.append(f"Total Sales: {context_json.get('total_sales')}")
        lines.append(f"Transactions: {context_json.get('num_transactions')}")
        lines.append(f"Avg Transaction Value: {context_json.get('avg_transaction_value')}")
        mg = context_json.get('mom_growth_pct')
        lines.append(f"MoM Growth %: {mg if mg is not None else 'N/A'}")
        lines.append("Top categories (sample):")
        for c in context_json.get('top_categories', [])[:5]:
            lines.append(str(c))
        return '\n'.join(lines)\n