curl -s "http://export.arxiv.org/api/query?max_results=100&search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending" \
    | ./xml2json.py \
    > arxiv-cs-LG.json
