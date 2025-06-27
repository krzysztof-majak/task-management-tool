from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router: APIRouter = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request) -> str:
    """
    Serves the root HTML page for the Task Management Tool.

    This endpoint returns a simple HTML page with a title, header, and links to the
    automatically generated API documentation using Swagger UI and ReDoc.

    Args:
        request (Request): The incoming HTTP request used to determine the base URL.

    Returns:
        str: A rendered HTML page with links to API documentation.
    """
    base_url = str(request.base_url).rstrip("/")
    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Task Management Tool - Home</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Inter', sans-serif;
                    padding: 3rem;
                    background-color: #eef2f5;
                    color: #34495e;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                    padding: 2.5rem 3rem;
                    max-width: 700px;
                    width: 100%;
                    text-align: center;
                }}
                h1 {{
                    color: #1a202c;
                    font-size: 2.8rem;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                h1 span {{
                    margin-left: 10px;
                }}
                h2 {{
                    color: #2d3748;
                    font-size: 1.8rem;
                    margin-top: 2.5rem;
                    margin-bottom: 1.5rem;
                }}
                p {{
                    font-size: 1.1rem;
                    margin-bottom: 1.5rem;
                    color: #4a5568;
                }}
                ul {{
                    list-style: none;
                    padding: 0;
                    margin-top: 2rem;
                }}
                li {{
                    margin-bottom: 1rem;
                }}
                a {{
                    text-decoration: none;
                    color: #4299e1;
                    font-weight: 600;
                    font-size: 1.1rem;
                    transition: color 0.3s ease, text-decoration 0.3s ease;
                }}
                a:hover {{
                    color: #2b6cb0;
                    text-decoration: underline;
                }}
                .emoji {{
                    font-size: 2.5rem;
                    vertical-align: middle;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1><span class="emoji">🧰</span> Task Management Tool</h1>
                
                <hr style="border: 0; height: 1px; background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.1), rgba(0, 0, 0, 0)); margin: 2rem 0;">

                <h2><span class="emoji">📘</span> API Documentation</h2>
                <ul>
                    <li><strong>Swagger UI:</strong> <a href="{base_url}/docs">{base_url}/docs</a></li>
                    <li><strong>ReDoc:</strong> <a href="{base_url}/redoc">{base_url}/redoc</a></li>
                </ul>
            </div>
        </body>
        </html>
    """
