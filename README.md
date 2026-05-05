# 🔍 AI News Verifier — GenLayer Bradbury Testnet

Submit any news headline → AI validators fetch the actual source → 
REAL / FAKE / MISLEADING verdict stored permanently on-chain.

## Files
- `index.html` — complete frontend (single file, no build needed)
- `news_verifier.py` — GenLayer Intelligent Contract

---

## STEP 1: Deploy Contract in GenLayer Studio

1. Go to **studio.genlayer.com**
2. Create a new project
3. Paste the contents of `news_verifier.py`
4. Select **Bradbury Testnet** in the network selector
5. Click **Deploy**
6. Copy your contract address (looks like `0x1234...`)

---

## STEP 2: Deploy Frontend to Vercel (iPad-friendly)

### Option A — GitHub + Vercel (recommended)

1. Go to **github.com** → New Repository → name it `ai-news-verifier`
2. Upload `index.html` (drag and drop works!)
3. Go to **vercel.com** → New Project → Import from GitHub
4. Select your repo → Framework: **Other** → Deploy
5. Done! Your site is live in ~30 seconds

### Option B — Direct Vercel Upload

1. Go to **vercel.com** → New Project
2. Drag the `index.html` file directly into Vercel
3. Deploy

---

## STEP 3: Connect Frontend to Your Contract

Once deployed, paste your contract address into the input field at the top of the site.
It saves automatically. No code editing needed!

---

## How the Contract Works

The `news_verifier.py` Intelligent Contract uses:

- `gl.get_webpage(url, mode="text")` — fetches the live source page
- `gl.exec_prompt(prompt)` — LLM analyzes headline vs page content  
- `gl.eq_principle_prompt_comparative()` — validators reach consensus on verdict
- On-chain storage — verdict stored permanently in contract state

---

## Network Info

- **Testnet**: Bradbury (shares RPC with Asimov)
- **Studio**: https://studio.genlayer.com
- **Faucet**: https://testnet-faucet.genlayer.foundation/
- **Portal**: https://portal.genlayer.foundation
