from dotenv import load_dotenv
import os
import discogs_client
import re
from typing import TypeAlias, Optional , Union, List, Dict
# Load the .env file
load_dotenv()

# Access the Discogs API token
discogs_api_token = os.getenv('DISCOGS_API_TOKEN')

d = discogs_client.Client('MatthewMusicApp/0.1', user_token=discogs_api_token)

"""here are some functions for the beginning, at first we only search by artist and album together"""


"""type aliases
////////
"""

ImageUrl: TypeAlias = str #type alias representing a URL to an image

"""////////"""

def search_album_by_title_and_artist(title,artist):
    results = d.search(title,artist=artist, type='release')
    return results.page(1)


"""function for extracting the release number from the list"""


def extract_release_numbers(release_list):
    release_numbers = []
    for release in release_list:
        # Find the number after "Release" using regex
        match = re.search(r'Release (\d+)', str(release))
        if match:
            release_numbers.append(int(match.group(1)))  # Append the number as an integer
    return release_numbers[0]  # Return the first number only


"""function to fetch the url from a dictionary for the images returned"""


def fetch_image_urls(data: dict) -> list[str]:
    """
    Fetch all image URLs ending in common image file extensions from a given dictionary.

    Args:
        data (dict): A dictionary potentially containing URLs.

    Returns:
        list[str]: A list of URLs ending with common image file extensions.
    """
    common_image_extensions = ('.jpeg', '.jpg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg')
    return next((value for value in data.values() if isinstance(value, str) and value.endswith(common_image_extensions)), None)



#ok now i need a function to fatch the img, then a function to fetch the tracklist, and a function fetch the title and arists name
# it would be good to somehow put that in a dictionary which is maybe convertable to json?
#//user search for an album and applies review, if the review is written it should put the album into the database of albums
#// and the review in the database of the reviews. finito?
####https://python3-discogs-client.readthedocs.io/en/latest/fetching_data.html


"""function to fetch the albums url"""


def fetch_image_url_by_getting_discogs_id(discogsid: int) -> Optional[str]:
    release = d.release(discogsid)
    if release.images:
        return release.images[0].uri
    return None



"""function to search for title"""


def search_album_by_title(title):
    pass


"""function to search for artist"""


def search_album_by_artist_name(artist_name):
    pass


"""function for getting tracklist as a dictionary key being number and value being track name"""


def generate_track_dict(tracks: list) -> dict[int, str]:
    """
    Generate a dictionary of track numbers and names.

    Args:
        tracks (list): A list of Track objects.

    Returns:
        dict[int, str]: A dictionary with track numbers as keys and track names as values.
    """
    return {index + 1: track.title for index, track in enumerate(tracks)}

"""function to generate release year"""


def get_release_year(album_id: int) -> int:

    release_year = d.release(only_number_for_test).year
    return release_year


try_release_results_kendrick = search_album_by_title_and_artist("to pimp a butterfly", "kendrick lamar")

only_number_for_test = extract_release_numbers(try_release_results_kendrick)

print(only_number_for_test)
print(d.release(only_number_for_test).formats)
print(fetch_image_url_by_getting_discogs_id(only_number_for_test))
hey = d.release(only_number_for_test).tracklist
track = hey[0]
print(track)
print(dir(track))
print(track.position)
print(generate_track_dict(hey))
print(d.release(only_number_for_test).year)
