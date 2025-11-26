# Digital Commerce Intelligence AI (Separated Files)
This project is a Streamlit application split into multiple files to keep code organized.

## Files
- `app.py` - main Streamlit app (UI, flow)
- `utils.py` - data ingestion, aggregation, plotting helpers
- `groq_client.py` - wrapper for Groq API (safe fallback if not configured)
- `requirements.txt`
- `sample_transactions.xlsx` - sample data for testing

## Quick start (local)
1. Create virtual env and install:
   ```
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the project root with:
   ```
   GROQ_API_KEY=your_key_here
   ```
   Or set GROQ_API_KEY in Streamlit Secrets when deploying to Streamlit Cloud.
3. Run:
   ```
   streamlit run app.py
   ```

## Notes
- Do NOT commit `.env` to GitHub.
- If Groq client/package name differs, adjust `groq_client.py`.
- The sample dataset is simple and for demo only.\n