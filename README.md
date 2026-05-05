# 🔍 AI News Verifier — GenLayer Bradbury Testnet

Submit any news headline → AI validators fetch the actual source → **REAL / FAKE / MISLEADING** verdict stored permanently on-chain.

---

## ⚠️ FIX: "Could not load contract schema" Error

This error happens because the original contract used `dict` instead of `TreeMap`.
The fixed contract in this zip uses `TreeMap[str, str]` which is required by GenLayer.

**What changed in `news_verifier.py`:**
```python
# ❌ OLD (causes schema error)
verifications: dict

# ✅ FIXED
verifications: TreeMap[str, str]
```

---

## STEP 1: Deploy Contract in GenLayer Studio

1. Go to **https://studio.genlayer.com**
2. Make sure you are on **Bradbury Testnet** (top-right network selector)
3. Click **New File** → name it `news_verifier.py`
4. Copy the **entire contents** of `news_verifier.py` from this zip and paste it
5. Click **Deploy** (bottom panel)
6. Wait for deployment — you'll see a contract address like `0xABCD...1234`
7. **Copy that contract address** — you'll need it for the frontend

> 💡 If you get a schema error, make sure line 7 says `verifications: TreeMap[str, str]`

---

## STEP 2: Get Test GEN Tokens (for gas)

1. Go to **https://testnet-faucet.genlayer.foundation/**
2. Connect your MetaMask wallet
3. Request test GEN tokens
4. Wait ~30 seconds for tokens to arrive

---

## STEP 3: Add GenLayer Bradbury to MetaMask

In MetaMask → Settings → Networks → Add Network:

| Field | Value |
|-------|-------|
| Network Name | GenLayer Bradbury Testnet |
| RPC URL | https://rpc.bradbury.genlayer.com |
| Chain ID | 127446 |
| Currency Symbol | GEN |
| Block Explorer | https://explorer.genlayer.foundation |

> ⚡ The frontend will try to add this automatically when you click "Connect MetaMask"

---

## STEP 4: Deploy Frontend to Vercel

### Option A — GitHub + Vercel (Recommended)

1. Go to **github.com** → click **New** → create repo named `ai-news-verifier`
2. Upload these files (drag & drop):
   - `index.html`
   - `vercel.json`
   - `news_verifier.py` (optional, for reference)
3. Go to **vercel.com** → **New Project**
4. Click **Import** → select your GitHub repo
5. Framework Preset: **Other**
6. Click **Deploy**
7. Done! Your URL will be `https://ai-news-verifier-xxxx.vercel.app`

### Option B — Direct Vercel Upload

1. Go to **vercel.com** → **New Project**
2. Drag the `index.html` file into the upload zone
3. Click **Deploy**

---

## STEP 5: Use the App

1. Open your Vercel URL
2. Click **🦊 Connect MetaMask** — approve the connection
3. Paste your **contract address** in the config box
4. Make sure **Live On-Chain** mode is selected
5. Type a news headline
6. Paste the source article URL
7. Click **Verify with AI Consensus**
8. Wait ~60-120 seconds for validators to reach consensus
9. Your verdict (REAL/FAKE/MISLEADING) is stored on-chain! 🎉

---

## STEP 6: Submit as GenLayer Contribution

1. Go to **https://portal.genlayer.foundation/#/submit-contribution**
2. Fill in:
   - **Project name**: AI News Verifier
   - **Description**: AI-powered on-chain news fact-checker using Intelligent Contracts
   - **GitHub URL**: your repo URL
   - **Live URL**: your Vercel deployment URL
   - **Contract address**: your deployed contract address
3. Submit!

---

## How the Contract Works

```
User submits headline + source URL
         ↓
Contract calls gl.get_webpage(source_url)  ← fetches live page
         ↓
Contract calls gl.exec_prompt(prompt)      ← LLM analyzes headline vs content
         ↓
gl.eq_principle_prompt_comparative()       ← multiple validators must agree
         ↓
Verdict stored in TreeMap on-chain         ← permanent, immutable
```

- `gl.get_webpage()` — fetches the live web page content
- `gl.exec_prompt()` — runs LLM analysis on content
- `gl.eq_principle_prompt_comparative()` — validators reach consensus
- `TreeMap[str, str]` — on-chain key/value storage

---

## Project Files

| File | Purpose |
|------|---------|
| `news_verifier.py` | GenLayer Intelligent Contract (deploy this in Studio) |
| `index.html` | Complete frontend with MetaMask wallet connect |
| `vercel.json` | Vercel deployment config |
| `README.md` | This guide |

---

## Troubleshooting

**"Could not load contract schema"**
→ Make sure you use `TreeMap[str, str]` not `dict` for the verifications field

**Transaction rejected by validators**
→ Check you have enough test GEN tokens from the faucet

**MetaMask won't connect**
→ Make sure MetaMask is installed, or use the MetaMask mobile browser

**Verdict not showing after finalization**
→ Wait a few more seconds, validators can take 60-120 seconds to reach consensus

**Wrong network error**
→ Add GenLayer Bradbury network to MetaMask using the chain details above

---

## Network Info

- **Testnet**: Bradbury
- **Studio**: https://studio.genlayer.com
- **Faucet**: https://testnet-faucet.genlayer.foundation/
- **Portal**: https://portal.genlayer.foundation
- **Explorer**: https://explorer.genlayer.foundation
- **Docs**: https://docs.genlayer.com
