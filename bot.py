import os
import requests
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# --------------------------------
# Load ENV
# --------------------------------

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

TMDB_BASE = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


# --------------------------------
# TMDB API FUNCTIONS
# --------------------------------

def trending_movies():
    url = f"{TMDB_BASE}/trending/movie/day"
    params = {"api_key": TMDB_API_KEY}

    r = requests.get(url, params=params)
    return r.json().get("results", [])


def top_movies():
    url = f"{TMDB_BASE}/movie/top_rated"
    params = {"api_key": TMDB_API_KEY}

    r = requests.get(url, params=params)
    return r.json().get("results", [])


def search_movies(query):

    url = f"{TMDB_BASE}/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": query
    }

    r = requests.get(url, params=params)

    return r.json().get("results", [])


def get_movie(movie_id):

    url = f"{TMDB_BASE}/movie/{movie_id}"

    params = {
        "api_key": TMDB_API_KEY,
        "append_to_response": "credits,videos,similar"
    }

    r = requests.get(url, params=params)

    return r.json()


# --------------------------------
# NETFLIX STYLE HOME MENU
# --------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [

        [
            InlineKeyboardButton("🔥 Trending", callback_data="trending"),
            InlineKeyboardButton("🏆 Top Rated", callback_data="top")
        ],

        [
            InlineKeyboardButton("🎭 Genres", callback_data="genres"),
            InlineKeyboardButton("🔎 Search Movie", callback_data="search")
        ]

    ]

    await update.message.reply_text(
        "🍿 *Movie Hub*\n\nBrowse movies like Netflix:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# --------------------------------
# MENU HANDLER
# --------------------------------

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "trending":

        movies = trending_movies()

        keyboard = []

        for m in movies[:10]:

            label = f"{m['title']} ⭐{m['vote_average']}"

            keyboard.append([
                InlineKeyboardButton(label, callback_data=f"movie_{m['id']}")
            ])

        keyboard.append(
            [InlineKeyboardButton("⬅ Back", callback_data="home")]
        )

        await query.edit_message_text(
            "🔥 *Trending Movies*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


    elif data == "top":

        movies = top_movies()

        keyboard = []

        for m in movies[:10]:

            label = f"{m['title']} ⭐{m['vote_average']}"

            keyboard.append([
                InlineKeyboardButton(label, callback_data=f"movie_{m['id']}")
            ])

        keyboard.append(
            [InlineKeyboardButton("⬅ Back", callback_data="home")]
        )

        await query.edit_message_text(
            "🏆 *Top Rated Movies*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


    elif data == "genres":

        keyboard = [

            [
                InlineKeyboardButton("🎬 Action", callback_data="genre_28"),
                InlineKeyboardButton("😂 Comedy", callback_data="genre_35")
            ],

            [
                InlineKeyboardButton("👻 Horror", callback_data="genre_27"),
                InlineKeyboardButton("🚀 Sci-Fi", callback_data="genre_878")
            ],

            [
                InlineKeyboardButton("❤️ Romance", callback_data="genre_10749")
            ],

            [
                InlineKeyboardButton("⬅ Back", callback_data="home")
            ]

        ]

        await query.edit_message_text(
            "🎭 *Select Genre*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


    elif data == "search":

        await query.edit_message_text(
            "🔎 Send me a movie name to search."
        )


    elif data == "home":

        await start(update, context)


# --------------------------------
# SEARCH HANDLER
# --------------------------------

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.message.text

    await update.message.reply_text("🔍 Searching...")

    movies = search_movies(query)

    if not movies:
        await update.message.reply_text("❌ No movies found.")
        return

    keyboard = []

    for m in movies[:5]:

        title = m["title"]
        year = m.get("release_date", "")[:4]
        rating = m["vote_average"]

        label = f"{title} ({year}) ⭐{rating}"

        keyboard.append([
            InlineKeyboardButton(label, callback_data=f"movie_{m['id']}")
        ])

    await update.message.reply_text(
        "Select a movie:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# --------------------------------
# MOVIE DETAIL
# --------------------------------

async def movie_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    movie_id = int(query.data.split("_")[1])

    await query.edit_message_text("Loading movie...")

    movie = get_movie(movie_id)

    title = movie.get("title")
    year = movie.get("release_date", "")[:4]
    rating = movie.get("vote_average")
    overview = movie.get("overview")

    genres = ", ".join([g["name"] for g in movie.get("genres", [])])

    cast = movie.get("credits", {}).get("cast", [])[:4]
    cast_names = ", ".join([c["name"] for c in cast])

    poster = movie.get("poster_path")

    cineby = f"https://www.cineby.gd/movie/{movie_id}"

    trailer = None

    for v in movie.get("videos", {}).get("results", []):

        if v["site"] == "YouTube":

            trailer = f"https://youtube.com/watch?v={v['key']}"
            break

    text = f"""
🎬 *{title}* ({year})

⭐ Rating: {rating}/10
🎭 Genres: {genres}
👥 Cast: {cast_names}

📖 *Overview*
{overview}
"""

    buttons = [

        [InlineKeyboardButton("▶ Watch Movie", url=cineby)],

        [InlineKeyboardButton("🎬 Similar Movies", callback_data=f"similar_{movie_id}")],

        [InlineKeyboardButton("⬅ Back to Menu", callback_data="home")]

    ]

    if trailer:
        buttons.insert(1, [InlineKeyboardButton("🎥 Trailer", url=trailer)])

    keyboard = InlineKeyboardMarkup(buttons)

    if poster:

        poster_url = IMAGE_BASE + poster

        await query.message.reply_photo(
            photo=poster_url,
            caption=text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    else:

        await query.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    await query.delete_message()


# --------------------------------
# SIMILAR MOVIES
# --------------------------------

async def similar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    movie_id = int(query.data.split("_")[1])

    movie = get_movie(movie_id)

    similar = movie.get("similar", {}).get("results", [])[:5]

    keyboard = []

    for m in similar:

        label = f"{m['title']} ⭐{m['vote_average']}"

        keyboard.append([
            InlineKeyboardButton(label, callback_data=f"movie_{m['id']}")
        ])

    keyboard.append(
        [InlineKeyboardButton("⬅ Back", callback_data="home")]
    )

    await query.edit_message_text(
        "🎬 Similar Movies",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# --------------------------------
# MAIN
# --------------------------------

def main():

    print("Bot starting...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(movie_callback, pattern="^movie_"))

    app.add_handler(CallbackQueryHandler(similar_callback, pattern="^similar_"))

    app.add_handler(CallbackQueryHandler(menu_callback))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search)
    )

    app.run_polling()


if __name__ == "__main__":
    main()