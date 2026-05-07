import uvicorn

if __name__ == "__main__":
    print("╔══════════════════════════════════════╗")
    print("║   Prompt Sidebar API  — port 8000    ║")
    print("║   Swagger docs → /docs               ║")
    print("╚══════════════════════════════════════╝")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
