# SmartGrowth AI - Quick Start Guide

## What's Been Built

A **production-ready Next.js dashboard** with 6 beautiful pages featuring:

| Page | Features |
|------|----------|
| **Overview** | KPIs, churn rate, revenue at risk, contracts & services breakdown |
| **Customer Analysis** | Individual lookup, churn probability gauge, risk assessment, recommendations |
| **Demand Forecast** | Multi-model comparison (Prophet/ARIMA/N-BEATS), metrics dashboard |
| **High Risk** | Risk distribution, spend vs churn scatter plot, ranked customer cards |
| **Batch Prediction** | Upload CSV or paste IDs, download results |
| **NLP Insights** | Semantic search, sentiment timeline, breakdown by channel |

## Run Locally

```bash
cd website
npm install
npm run dev
```

Open http://localhost:3000

## Deploy to Vercel (Recommended)

```bash
cd website
vercel deploy
```

Or connect your GitHub repo to  Vercel for automatic deployments.

## Environment Setup

The `.env.local` file is pre-configured to use your backend:
```
NEXT_PUBLIC_API_URL=https://handhelds-cooling-gale-consistently.trycloudflare.com
```

## Architecture

```
Vercel (Frontend)
       ↓ HTTPS
  Next.js App
       ↓ API calls
Cloudflare Tunnel
       ↓ SSh
  GCP VM (Backend)
```

## Key Features

✅ Dark theme optimized for extended use  
✅ Fully responsive (mobile to desktop)  
✅ Real-time API integration  
✅ TypeScript safe  
✅ Zero-downtime deployment  
✅ Automatic caching  
✅ Professional color system  

## File Structure

```
website/
├── app/
│   ├── page.tsx              # Overview dashboard
│   ├── layout.tsx            # Root layout with sidebar
│   ├── customer-analysis/    # Customer lookup
│   ├── forecast/             # Demand forecasting
│   ├── high-risk/            # Risk management
│   ├── batch/                # Bulk predictions
│   └── nlp/                  # NLP insights
├── components/
│   ├── layout.tsx            # Navigation sidebar
│   ├── ui.tsx                # Reusable components
│   └── charts.tsx            # Chart components
└── lib/
    ├── api.ts                # API client
    └── constants.ts          # Design system
```

## What's Connected to Your Backend

- ✅ Churn prediction (single & batch)
- ✅ Customer data retrieval
- ✅ Demand forecasting (all 3 models)
- ✅ High-risk customer scanning
- ✅ Semantic search
- ✅ Sentiment analysis

## Next Steps

1. **Test locally**: `npm run dev`
2. **Deploy**: `vercel deploy`
3. **Share link**: Get a public HTTPS URL
4. **Monitor**: Backend is already on Cloudflare Tunnel

## Customization

- **Colors**: Edit `lib/constants.ts`
- **API URL**: Change `next.public_api_url` in `.env.local`
- **Add pages**: Create new folder in `app/`

---

Everything is ready to go! 🚀
