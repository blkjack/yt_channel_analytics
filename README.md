# YT Channel Analytics

![YT Channel Analytics](https://github.com/yildiramdsa/yt_channel_analytics/blob/main/yt_logo_lg.png)

This **Streamlit app** provides insights into **YouTube channel performance**, tracking subscriber growth, views, watch hours, likes, comments, and shares. It supports daily, weekly, monthly, and quarterly trends with interactive charts and thoughtful insights, allowing users to analyze engagement, visualize trends, and filter data by custom date ranges.

https://yildiramdsa-yt-channel-analytics-yt-channel-analytics-h9ai9c.streamlit.app/

## Live channel data via SearchApi

The bundled CSV is a single synthetic channel. To look at **any public channel**, the app can pull live data through [SearchApi](https://www.searchapi.io)'s YouTube Channel engine, with no YouTube Data API quota or OAuth setup needed.

1. Get an API key at [searchapi.io](https://www.searchapi.io).
2. Provide it either as an environment variable or as a Streamlit secret:
   ```bash
   export SEARCHAPI_API_KEY=your_key
   # or, in .streamlit/secrets.toml:
   # SEARCHAPI_API_KEY = "your_key"
   ```
3. Run `streamlit run yt_channel_analytics.py` and paste a channel ID (`UC...`) into **Live Channel** in the sidebar.

You can also use the client on its own:

```python
from searchapi_youtube import SearchApiYouTube

channel, videos = SearchApiYouTube().fetch_channel("UC_x5XG1OV2P6uZZ5FSM9Ttw")
print(channel["TITLE"], channel["SUBSCRIBERS"])
print(videos[["PUBLISHED", "TITLE", "VIEWS"]].tail())
```

Results are cached for an hour so the app doesn't spend searches on every rerun. Run the tests with `pip install pytest && pytest`.
