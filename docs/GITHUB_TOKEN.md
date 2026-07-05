# How to Get GitHub Token

## Step-by-Step Instructions

### 1. Go to GitHub Settings
- Log in to your GitHub account
- Click on your profile picture (top right)
- Select **Settings**

### 2. Navigate to Developer Settings
- Scroll down to the bottom of the left sidebar
- Click **Developer settings**

### 3. Create Personal Access Token
- Click **Personal access tokens**
- Select **Tokens (classic)**
- Click **Generate new token**
- Select **Generate new token (classic)**

### 4. Configure the Token
- **Note**: Give it a name like "TGIndex Bot"
- **Expiration**: Select 90 days (or No expiration)
- **Select scopes**: Check only `public_repo` (for public repository access)

### 5. Generate and Copy
- Click **Generate token**
- **IMPORTANT**: Copy the token immediately! You won't see it again.

### 6. Add to .env File
Open your `.env` file and add:

```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

Replace `ghp_xxxxxxxxxxxxxxxxxxxx` with your actual token.

## Why Do You Need It?

Without a token:
- GitHub allows only 10 requests per minute
- You'll get 401 errors quickly

With a token:
- GitHub allows 30 requests per minute
- More search results
- No authentication errors

## Testing

After adding the token, restart the server:

```bash
python -m app.main
```

Check the logs - you should see more results from GitHub.
