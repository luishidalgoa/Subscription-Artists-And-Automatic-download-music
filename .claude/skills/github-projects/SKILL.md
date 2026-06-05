---
name: github-projects
description: >-
  Gestionar GitHub Projects (v2) de luishidalgoa por la API GraphQL con curl
  (el CLI `gh` NO está instalado en este host). Úsalo para organizar tareas,
  roadmaps o backlogs de mejoras: crear un project, añadir campos (Priority,
  Status), crear issues y enlazarlos al project, y fijar valores de campo.
---

# GitHub Projects (v2) sin `gh`

En este host **no hay `gh`**, así que todo se hace con `curl` contra
`https://api.github.com/graphql` (Projects v2 **solo** existe en GraphQL; la API
REST de "projects" clásicos está deprecada). Las issues sí se crean por REST.

## 0. Token

Projects v2 necesita un PAT con scopes **`project`** y **`repo`**. El helper lee el
token de `$GITHUB_TOKEN`; si no está, cae a `/tmp/ghpat` (token efímero de la sesión).

```bash
export GITHUB_TOKEN="$(cat /tmp/ghpat 2>/dev/null)"
# Comprueba scopes (debe incluir project y repo):
curl -sI -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep -i x-oauth-scopes
```

**Seguridad:** nunca escribas el token en ficheros versionados ni en la URL del
remote. Al imprimir salidas, redacta con `sed -E 's/gh[ps]_[A-Za-z0-9_]+/<REDACTED>/g'`.

## 1. IDs que necesitas

```bash
# owner (viewer) id
gql(){ curl -s -H "Authorization: bearer $GITHUB_TOKEN" -H "Content-Type: application/json" -d "$1" https://api.github.com/graphql; }

gql '{"query":"query{viewer{id login}}"}'
# Lista de projects del usuario:
gql '{"query":"query{viewer{projectsV2(first:30){nodes{id number title url closed}}}}"}'
# node_id de un repo (para enlazar el project al repo):
curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/OWNER/REPO | python3 -c "import sys,json;print(json.load(sys.stdin)['node_id'])"
```

## 2. Crear un project y enlazarlo a un repo

```bash
# createProjectV2(ownerId,title) -> id, number
gql '{"query":"mutation($o:ID!,$t:String!){createProjectV2(input:{ownerId:$o,title:$t}){projectV2{id number url}}}","variables":{"o":"<OWNER_ID>","t":"Mi Roadmap"}}'
# Enlazar el repo al project (aparece en la pestaña Projects del repo):
gql '{"query":"mutation($p:ID!,$r:ID!){linkProjectV2ToRepository(input:{projectId:$p,repositoryId:$r}){repository{name}}}","variables":{"p":"<PROJECT_ID>","r":"<REPO_NODE_ID>"}}'
```

## 3. Campos del project

Un project nuevo trae los campos `Title` y `Status` (single-select: Todo / In
Progress / Done). Listarlos (con las opciones de los single-select):

```bash
gql '{"query":"query($p:ID!){node(id:$p){... on ProjectV2{fields(first:30){nodes{__typename ... on ProjectV2FieldCommon{id name} ... on ProjectV2SingleSelectField{id name options{id name}}}}}}}","variables":{"p":"<PROJECT_ID>"}}'
```

Crear un campo **Priority** (single-select). Las opciones necesitan `color`
(`GRAY|BLUE|GREEN|YELLOW|ORANGE|RED|PURPLE|PINK`) y `description` (puede ir vacío):

```bash
gql '{"query":"mutation($p:ID!){createProjectV2Field(input:{projectId:$p,dataType:SINGLE_SELECT,name:\"Priority\",singleSelectOptions:[{name:\"P1\",color:RED,description:\"\"},{name:\"P2\",color:ORANGE,description:\"\"},{name:\"P3\",color:YELLOW,description:\"\"},{name:\"P4\",color:GRAY,description:\"\"}]}){projectV2Field{... on ProjectV2SingleSelectField{id name options{id name}}}}}","variables":{"p":"<PROJECT_ID>"}}'
```

## 4. Crear issues y añadirlas al project

Issue por REST (más simple que GraphQL), luego enlazar por su `node_id`:

```bash
# Crear issue -> devuelve node_id y number
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/issues \
  -d '{"title":"Mi tarea","body":"Descripción...","labels":["enhancement"]}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['node_id'],d['number'])"

# Añadir la issue al project -> devuelve el item id (distinto del issue id)
gql '{"query":"mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}","variables":{"p":"<PROJECT_ID>","c":"<ISSUE_NODE_ID>"}}'
```

Sin crear issue (item "draft", vive solo en el project):

```bash
gql '{"query":"mutation($p:ID!,$t:String!,$b:String!){addProjectV2DraftIssue(input:{projectId:$p,title:$t,body:$b}){projectItem{id}}}","variables":{"p":"<PROJECT_ID>","t":"Tarea","b":"Cuerpo"}}'
```

## 5. Fijar valores de campo (Priority, Status)

Para single-select se pasa el **id de la opción** (de los listados en el paso 3):

```bash
gql '{"query":"mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}}","variables":{"p":"<PROJECT_ID>","i":"<ITEM_ID>","f":"<FIELD_ID>","o":"<OPTION_ID>"}}'
```

Otros tipos de valor: `{text:"..."}`, `{number:3}`, `{date:"2026-06-05"}`,
`{iterationId:"..."}`.

## Helper

`gh_projects.py` (en esta carpeta) envuelve lo anterior:

```bash
export GITHUB_TOKEN="$(cat /tmp/ghpat)"
python3 .claude/skills/github-projects/gh_projects.py list-projects
python3 .claude/skills/github-projects/gh_projects.py fields <PROJECT_ID>
```

## Gotchas

- El **item id** (en el project) ≠ **issue/content id**. Guarda ambos.
- `createProjectV2Field` exige `color` y `description` en cada opción single-select;
  omitirlos da error de validación.
- Projects v2 es **por usuario u organización**, no "por repo": se crea bajo el owner
  y se *enlaza* al repo con `linkProjectV2ToRepository`.
- GraphQL devuelve `200 OK` aunque haya `errors` en el body: comprueba siempre
  `.errors` antes de dar algo por hecho.
- Rate/secondary limits: si automatizas muchos items, mete `sleep` entre mutaciones.
