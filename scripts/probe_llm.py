import httpx

host = "161.24.23.15"
key = "Z_qYDPDbUYYxxeiT53cAeTAKifAmbfo6eMNWyZLAuug"
ports = [11434, 3000, 8080, 8000, 11435, 5000, 8888, 1234, 443]
paths = ["/", "/api/tags", "/v1/models", "/ollama/api/tags", "/api/models", "/openai/v1/models"]

for p in ports:
    refused = False
    for path in paths:
        url = f"http://{host}:{p}{path}"
        try:
            r = httpx.get(
                url,
                headers={"Authorization": f"Bearer {key}"},
                timeout=3.0,
                follow_redirects=True,
            )
            body = r.text[:160].replace("\n", " ")
            print(f"{r.status_code} {url} :: {body}")
        except Exception as e:
            err = str(e)
            if "10061" in err or "refused" in err.lower():
                if path == "/":
                    print(f"REFUSED {host}:{p}")
                refused = True
                break
            print(f"ERR {url} :: {err[:100]}")
    if refused:
        continue
