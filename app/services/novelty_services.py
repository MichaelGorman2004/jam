import requests
import openai
import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from moviepy.editor import VideoFileClip
from urllib.parse import urlparse


class NoveltyEvaluator:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')

    # Audio = True if mp3 file, Audio = False if mp4 file (video file)
    def evaluate_novelty(self, project_repo_url, audio, presentation_file_path):

        presentation_summary = self._build_project_summary(presentation_file_path=presentation_file_path, audio=audio)
        github_cosine_similarity, github_repo, gh_repo_summary, proj_readme_summary = self._get_github_cosine_similarity(presentation_summary, project_repo_url)
        google_cosine_similarity, google_article, google_article_summary = self._get_google_cosine_similarity(presentation_summary)

        github_score = round((1 - github_cosine_similarity) * 100.0, 1)
        google_score = round((1 - google_cosine_similarity) * 100.0, 1)
        overall_score = round((github_score + google_score) / 2, 1)

        github_summary = f'This project is not similar to any other projects found on GitHub. This helped you score a {github_score} out of 100 for your GitHub novelty score.'
        if github_score > 60:
            github_summary = f'This project is similar to a project found on GitHub. '
            github_summary += self._make_openai_request(
                f'Here is a summary of a users github README file for a project they worked on: {proj_readme_summary}. Here is a summary of a github repository project that was found online: {gh_repo_summary}. These summaries are similar. In a few sentences, explain why these projects are similar.'
            )

        google_summary = f'This project is not similar to any other articles found on Google. This helped you score a {google_score} out of 100 for your Google novelty score.'
        if google_score > 60:
            google_summary = f'This project is similar to an article found on Google. '
            google_summary += self._make_openai_request(
                f'Here is a summary of a google article about a topic: Title: {google_article_summary}. Here is a summary of a presentation of about a project: {presentation_summary}. In a few sentences, explain why the Google article is similar to the project.'
            )

        response_json = {
            'github_score': github_score,
            'github_repo': github_repo['name'],
            'github_repo_link': github_repo['html_url'],
            'github_summary': github_summary,
            'google_score': google_score,
            'google_article': google_article['title'],
            'google_article_link': google_article['link'],
            'google_summary': google_summary,
            'overall_score': overall_score,
            'presentation_summary': presentation_summary
        }
        return response_json


    def _get_github_cosine_similarity(self, presentation_summary, project_repo_url):
        not_keywords = False
        iter = 0
        keywords = ''
        while not_keywords and iter < 10:
            keywords = self._make_openai_request(f'Here is a summary of a presentation about a project, please provide a 5 word title or 5 key words of this presentation separated by spaces. Do not include anything else in your response. It should only be 5 words separated by spaces. {presentation_summary}')
            not_keywords = True if len(keywords.split(' ')) == 5 else False
            iter += 1
        if iter == 10:
            raise ValueError('Could not generate keywords in 10 attempts')
        repo_readme = self._fetch_readme(project_repo_url)
        project_readme_summary = self._make_openai_request(
            f'Here is a project github repo README file: {repo_readme}. Please provide a summary of the project in a couple sentences.'
        )
        repos = self._search_github_repos(keywords)
        max_cosine_similarity = 0
        max_repo = None
        max_repo_summary = ''
        for repo in repos:
            readme = self._fetch_readme(repo['url'])
            if readme is not None:
                readme_summary = self._make_openai_request(
                    f'Here is a project README file of a github repo: {readme}. Please provide a summary of the project in a couple sentences.'
                )
                cosine_similarity = self._get_cosine_similarity(project_readme_summary, readme_summary)
                if cosine_similarity > max_cosine_similarity:
                    max_cosine_similarity = cosine_similarity
                    max_repo = repo
                    max_repo_summary = readme_summary
        return max_cosine_similarity, max_repo, max_repo_summary, project_readme_summary
    

    def _get_google_cosine_similarity(self, presentation_summary):
        results = self._fetch_google_results(presentation_summary)
        articles = self._extract_article_info(results)
        max_cosine_similarity = 0
        max_article = None
        max_article_summary = ''
        for article in articles:
            article_summary = self._make_openai_request(
                f'Here is an article about a topic: Title: {article['title']}. Snippet: {article['snippet']}. Description: {article['description']}. Please provide a summary of the topic in a couple sentences.'
            )
            cosine_similarity = self._get_cosine_similarity(presentation_summary, article_summary)
            if cosine_similarity > max_cosine_similarity:
                max_cosine_similarity = cosine_similarity
                max_article = article
                max_article_summary = article_summary
        return max_cosine_similarity, max_article, max_article_summary


    def parse_github_repo_url(self, repo_url):
        """
        Parses a GitHub repository URL and extracts the owner and repository name.

        Args:
            repo_url (str): The GitHub repository URL.

        Returns:
            tuple: A tuple containing the owner and repository name (owner, repo_name).
        """
        parsed_url = urlparse(repo_url)
        
        # Split the path to get the parts after 'github.com'
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo_name = path_parts[1]
            return owner, repo_name
        else:
            raise ValueError("Invalid GitHub repository URL format")


    def _fetch_google_results(self, query):
        # SerpAPI endpoint URL
        url = 'https://www.searchapi.io/api/v1/search'
        params = json.dumps({
            'q': query,  # Search query
            'hl': 'en',  # English
            'gl': 'us',  # Only US results
            'api_key': os.getenv('SERP_API_KEY'),  # API key
            'num': 10  # Number of results to fetch
        })

        response = requests.get(url=url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error: {response.status_code}, {response.text}')
            return None
        

    def _extract_article_info(self, results):
        print(results['organic_results'])
        if 'organic_results' in results:
            articles = []
            for result in results['organic_results']:
                title = result.get('title')
                link = result.get('link')
                snippet = result.get('snippet')
                description = result.get('description')
                articles.append({'title': title, 'link': link, 'snippet': snippet, 'description': description})
            return articles
        else:
            return []


    def _search_github_repos(self, query, per_page=10):
        url = 'https://api.github.com/search/repositories'
        params = {
            'q': query,          # Search query
            'per_page': per_page # Number of results per page
        }
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()['items']
        else:
            print(f"Error: {response.status_code}")
            return []
        
    
    def _fetch_readme(self, url):
        owner, repo_name = self.parse_github_repo_url(url)
        url = f'https://api.github.com/repos/{owner}/{repo_name}/readme'
        headers = {
            'Accept': 'application/vnd.github.v3.raw+json'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return None
    

    def _make_openai_request(self, prompt):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        try:
            response = openai.ChatCompletion.create(
                model='gpt-4',
                messages=[
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            raise ValueError(f'OpenAI Error: {e}')


    def _build_project_summary(self, presentation_file_path, audio):
        if audio:
            presentation_transcription = self._transcribe_mp3(presentation_file_path)
        else:
            presentation_transcription = self._transcribe_mp4(presentation_file_path)
        summary = self._make_openai_request(
            f'Here is a transcription of a project presentation, {presentation_transcription}. Please provide a summary of the project in a couple sentences.'
        )
        return summary


    def _get_cosine_similarity(self, str1, str2):
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform([str1, str2])
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)[0][1]


    def _transcribe_mp4(self, file_path):
        """
        Takes an MP4 file, extracts the audio, and transcribes it using OpenAI's Whisper API.

        Args:
            file_path (str): The path to the MP4 file.

        Returns:
            str: The transcribed text.
        """
        openai.api_key = os.getenv('OPENAI_API_KEY')
        try:
            audio_file_path = self._extract_audio_from_video(file_path)
            transcription = self._transcribe_mp3(audio_file_path)
            os.remove(audio_file_path)
            return transcription
        except Exception as e:
            return f"An error occurred: {str(e)}"


    def _extract_audio_from_video(self, video_path):
        """
        Extracts audio from an MP4 video file and saves it as an MP3 file.

        Args:
            video_path (str): The path to the MP4 file.

        Returns:
            str: The path to the extracted MP3 file.
        """
        audio_file_path = video_path.replace('.mp4', '.mp3')
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_file_path)
        return audio_file_path


    def _transcribe_mp3(self, audio_file_path):
        """
        Transcribes an audio file using OpenAI's Whisper API.

        Args:
            audio_file_path (str): The path to the audio file (MP3).

        Returns:
            str: The transcribed text.
        """
        with open(audio_file_path, 'rb') as audio_file:
            response = openai.Audio.transcribe('whisper-1', audio_file)
        return response['text']
