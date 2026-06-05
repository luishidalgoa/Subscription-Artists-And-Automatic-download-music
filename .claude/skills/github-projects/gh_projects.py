#!/usr/bin/env python3
"""Helper minimalista para GitHub Projects (v2) por GraphQL — el CLI `gh` no está
instalado en este host.

Token: se lee de $GITHUB_TOKEN; si no, de /tmp/ghpat. Necesita scopes project + repo.

Uso:
    export GITHUB_TOKEN="$(cat /tmp/ghpat)"
    python3 gh_projects.py list-projects
    python3 gh_projects.py fields <PROJECT_ID>
    python3 gh_projects.py create-project "<OWNER_ID>" "Titulo"
    python3 gh_projects.py add-issue <PROJECT_ID> <ISSUE_NODE_ID>
    python3 gh_projects.py set-select <PROJECT_ID> <ITEM_ID> <FIELD_ID> <OPTION_ID>
"""
import json
import os
import sys
import urllib.request

API = "https://api.github.com/graphql"


def _token() -> str:
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        try:
            with open("/tmp/ghpat") as f:
                tok = f.read().strip()
        except OSError:
            pass
    if not tok:
        sys.exit("No hay token: define $GITHUB_TOKEN o /tmp/ghpat")
    return tok


def gql(query: str, variables: dict | None = None) -> dict:
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {_token()}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    if data.get("errors"):
        sys.exit("GraphQL errors: " + json.dumps(data["errors"], ensure_ascii=False))
    return data["data"]


def list_projects():
    d = gql("query{viewer{projectsV2(first:30){nodes{id number title url closed}}}}")
    for p in d["viewer"]["projectsV2"]["nodes"]:
        print(f"#{p['number']:>3} | {p['id']} | closed={p['closed']!s:5} | {p['title']}")


def fields(project_id: str):
    q = """query($p:ID!){node(id:$p){... on ProjectV2{fields(first:30){nodes{
      __typename
      ... on ProjectV2FieldCommon{id name}
      ... on ProjectV2SingleSelectField{id name options{id name}}
    }}}}}"""
    d = gql(q, {"p": project_id})
    for f in d["node"]["fields"]["nodes"]:
        line = f"{f.get('name','?'):16} | {f.get('id','')} | {f['__typename']}"
        if f.get("options"):
            line += " :: " + ", ".join(f"{o['name']}={o['id']}" for o in f["options"])
        print(line)


def create_project(owner_id: str, title: str):
    q = """mutation($o:ID!,$t:String!){createProjectV2(input:{ownerId:$o,title:$t}){
      projectV2{id number url}}}"""
    d = gql(q, {"o": owner_id, "t": title})
    p = d["createProjectV2"]["projectV2"]
    print(json.dumps(p))


def add_issue(project_id: str, content_id: str):
    q = """mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){
      item{id}}}"""
    d = gql(q, {"p": project_id, "c": content_id})
    print(d["addProjectV2ItemById"]["item"]["id"])


def set_select(project_id: str, item_id: str, field_id: str, option_id: str):
    q = """mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(
      input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){
      projectV2Item{id}}}"""
    gql(q, {"p": project_id, "i": item_id, "f": field_id, "o": option_id})
    print("ok")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, *rest = sys.argv[1:]
    {
        "list-projects": lambda: list_projects(),
        "fields": lambda: fields(*rest),
        "create-project": lambda: create_project(*rest),
        "add-issue": lambda: add_issue(*rest),
        "set-select": lambda: set_select(*rest),
    }.get(cmd, lambda: sys.exit(f"comando desconocido: {cmd}"))()


if __name__ == "__main__":
    main()
