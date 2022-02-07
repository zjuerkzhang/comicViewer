# A Simple Comic/Photo/Picture Viewer Web App

## Introduction
- Based on web.py with tiny size
- Generate Web Structure tree basing on the file structure which storing the pictures
- Simple deployment

## Deployment
### Pre-condition
- web.py: pip3 install web.py

### Instruction
- git clone to your local host
- `cd comicViewer; mkdir comic`
- copy your pictures with directory into the newly-created directory comic
- `python3 src/main.py 127.0.0.1:[port]`
- access http://127.0.0.1:[port]

### Nginx Redirect Adaption
If you want to deploy this app after the nginx with `proxy_pass`, you need to change the parameter `nginxRedirectPath` in page.html; otherwise, you need to assign empty string '' to it.

