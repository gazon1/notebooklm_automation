<h1>NotebookLM source automation</h1>
<a id="readme-top"></a>

<h2>The problem</h2>

Google's [NotebookLM](https://notebooklm.google.com/) is a tool - powered by Google Gemini - that allows us to quickly generate resources like study guides, briefing documents and audio overviews. To create these assets, we need to make a new notebook and provide sources that the model can then pull from. These sources can be:

- File uploads (PDF, .txt, markdown & audio i.e. mp3)
- Google drive: Docs or Slides
- Links: Website or YouTube
- Paste text: Manually paste in text like meeting notes

However, as pointed out by colleagues and in various Reddit posts, the process for adding link-based sources is incredibly cumbersome; users need to continuously:

- Press 'Add source'
- Select 'Website' or 'YouTube'
- Paste the source URL
- Hit enter/press 'Insert'

This might be fine for a handful of sources but, given you can create notebooks of up to 300 sources, this is less than ideal when scaled.

<h2>The solution</h2>

Given we have a repeated pattern of behaviour in terms of how sources are added, this process is a perfect candidate for browser automation, and that's exactly what is used here. Using [Playwright](https://playwright.dev/python/) - a library created specifically for end-to-end testing and general browser automation tooling - we can easily loop through the steps outlined above to create a new notebook populated with your desired sources.