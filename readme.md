# Golf Launch Monitor Dashboard

This is a mobile-friendly, interactive dashboard built with **Streamlit** to visualize and analyze data from a golf launch monitor (e.g., Swing Caddie SC4).

## 📊 Features
- **Dispersion Plot** (Carry vs. Offline by club)
- **Club Gapping Chart** (Average Carry per club)
- **Interactive Filters** (Select clubs to analyze)
- **Shot Table** (View raw launch monitor data)

## 📁 Files
- `app.py` — Main Streamlit app code
- `golfdata.csv` — Your launch monitor data (CSV format)

## 📦 How to Deploy on Streamlit Cloud
1. Create a free GitHub repository
2. Upload both `app.py` and `golfdata.csv` to the repository
3. Go to [https://streamlit.io/cloud](https://streamlit.io/cloud)
4. Click **"New App"** and connect your GitHub repository
5. Select the `main` branch and `app.py` as the entry point
6. Click **Deploy**

## 📱 Add to iPhone Home Screen
1. Open your deployed app in **Safari**
2. Tap the **Share** icon → **Add to Home Screen**
3. The dashboard now works like a native app!

## 📝 Data Requirements
Your `golfdata.csv` file should contain the following columns:
- `Club`
- `Carry(yd)`
- `Offline(yd)`
- `Total(yd)`
- `Ball Speed(mph)`
- `Launch Angle`
- `Spin Rate`

Make sure the first row contains headers and there are no merged cells or multi-row headers.

## 🔧 Customization Ideas
- Add export/download button
- Add club-by-club standard deviation
- Add comparison between rounds
- Include wind/weather metadata if available

---
Built with ❤️ using [Streamlit](https://streamlit.io).

