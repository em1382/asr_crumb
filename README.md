## Crumb: the back-end of All Seeding Rye

Crumb is the back-end of a refresher project I built in preparation for interviews. I wanted to make sure I actually remembered how to work effectively on the back-end after spending a great deal of time in the cloud and on the front-end in my last full-time position.

It's intended to be a light-hearted toy "fit-to-standard" project that ingests bread ingredients and passes them to a model (for now, only Gemini Flash 2.5) for review.

The project proposal for this application can be found [here](https://docs.google.com/document/d/1piazBpKitfWhJgxqDaO3vAHaw_MUYFVNsVBnu0-WlLU/edit?usp=sharing).

#### Quick Note on Front-end
A sister project, [Crust](https://github.com/em1382/asr_crust), serves as this application's front-end and presentation layer. Once the back-end set-up is complete, I'd suggest heading over there for additional local project setup.

### Getting Started
In order to get a local development environment up and running, you'll need to first create a virtual environment with `venv`:
```bash
$ python3.14 -m venv .venv
```
Then activate it with:
```bash
$ source ./.venv/bin/activate
```

Once your virtual environment is set up, you can install dependencies for the project with:
```bash
$ pip install -r requirements.txt
```

### Architectural Dependencies
#### Database
You'll need a PostgreSQL database instance running in order to use Crumb. For convenience, a docker-compose.yaml to spin up a container with v16 is included in the project root (assuming you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed).
```bash
$ docker compose up -d
```
#### Google Gemini API Key
You'll need a Google Gemini API key for interaction with the LLM. A key can be obtained for free (with a valid Google Account) from https://aistudio.google.com/api-keys.

### Required Environment Variables
Once requirements are installed, you'll need to configure a few environment variables before starting the project.

- `DATABASE_URL`: a PostgreSQL connection string to an empty database.
- `API_V1_STR`: the endpoint prefix for API routes (Crust expects `/api/v1`).
- `CORS_ALLOWED_ORIGINS`: allowed origins for client requests.
- `CRUMB_API_KEY`: the key which you'll use to interact with the REST API endpoints via an `X-Api-Key` HTTP header.
- `GOOGLE_API_KEY`: your Google Gemini API key, which will be used to interact with Gemini via LangChain APIs.

Create a .env file in the root of the project and populate with your values. You can a template in .env.example in the project root.

### Alembic Migrations
This project uses [Alembic](https://alembic.sqlalchemy.org/en/latest/) to handle database migrations. After you configure a local database and set the `DATABASE_URL` environment variable, you can run initial migrations using:
```bash
$ alembic upgrade head
```

This will generate the application's initial schema in your database and is the last step before actually starting the application!

### Running the Application (Development)
Once your .env file is populated, you can run the application in development mode with:
```bash
$ fastapi dev
```

This will start the development server bundled with FastAPI and start your application by default on port 8000.

### Using the Application
Ingest is API-only at the moment. The OpenAPI docs for the app can be found at http://localhost:8000/docs.
For interaction with the API, I'd recommend [Postman](https://postman.com).

In order for Crumb to create recommendations based on your list of ingredients, send an HTTP POST request (with an `X-API-Key` header set to `CRUMB_API_KEY`) to http://localhost:8000/api/v1/recipes with the following payload:
```json
{
    "batch_id": "b_1125",
    "recipe_name": "Definitely Not Optimal Artisan Sourdough",
    "status_expectation": "optimal",
    "ingredients": [
        {
            "name": "bread_flour",
            "amount": 10000000,
            "unit": "grams"
        },
        {
            "name": "whole_wheat_flour",
            "amount": 200,
            "unit": "grams"
        },
        {
            "name": "water",
            "amount": 700,
            "unit": "grams"
        },
        {
            "name": "active_sourdough_starter",
            "amount": 200,
            "unit": "grams"
        },
        {
            "name": "salt",
            "amount": 20,
            "unit": "grams"
        }
    ]
}
```
A new `Recipe` will be created in corresponding database table, and a background task will send the ingredients to the LLM for recommendations.

#### Note
The status expectation is stored, but exists for demo purposes only. The LLM determines the quality of the recipe based on the ingredients list alone.

Once the LLM finishes running, a new `FitRecommendation` is created in the related database table for that specific `FitRun`.

Making a GET request to http://localhost:8000/api/v1/recipes/{id}/fit-runs will allow you to see the recommendations the model has made if you aren't running the application alongside Crust.

```JSON
{
    "data": [
        {
            "recipe_id": 1,
            "run_sequence": 1,
            "agent_model": "gemini-2.5-flash",
            "status": "needs_review",
            "id": 1,
            "created_at": "2026-04-11T22:34:51.660115Z",
            "recommendations": [
                {
                    "severity": "error",
                    "message": "The amount of bread flour is extremely disproportionate to the other ingredients, making the recipe unworkable.",
                    "reasoning": "With 10,000,000 grams of flour, the water, salt, and sourdough starter percentages are critically low (0.0075% hydration, 0.0002% salt, 0.002% starter). This would result in an impossibly dry, unmixable, and unfermentable dough. It appears the flour quantity is a significant typo.",
                    "recommendations": [
                        "Adjust the flour amount to a standard quantity for a single sourdough boule, such as 1000 grams.",
                        "If the flour amount was intended to be 10,000,000 grams, then all other ingredients would need to be scaled up by a factor of 10,000 to achieve proper ratios, which is impractical for a single batch.",
                        "For a 1000g flour sourdough boule, the current amounts of water (750g), salt (20g), and sourdough starter (200g) would be appropriate, yielding a 75% hydration, 2% salt, and 20% starter dough."
                    ],
                    "id": 1,
                    "fit_run_id": 1
                }
            ]
        }
    ]
}
```

As this is a demo application, the API is currently lacking a full featureset. New API endpoints are planned to allow for more intuitive interaction with the API.

### Next Steps
- Fine-tuning for prompt passed to model (the model currently is far too strict).
- Ability to update a recipe and have new recommendations run.
- Ability to retry failed runs, or run recommendations again for the same recipe.
- Logging! Would probably opt for a structured logger.
 - Potentially an integration with Sentry.
- User accounts, authentication.
  - Potentially can integrate with Auth0, as they have a free tier.
- Rate-limiting for APIs.
- Require auth for all reads.
- Integration tests.
- Complete crud for all resources.
- Architecture diagram in README.