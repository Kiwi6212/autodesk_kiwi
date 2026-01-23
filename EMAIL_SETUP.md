# Configuration E-mail pour AutoDesk Kiwi

Ce guide vous explique comment configurer l'accès aux e-mails Outlook et Protonmail.

## 📧 Configuration Outlook (Microsoft 365)

### Étape 1: Créer une application Azure AD

1. Allez sur [Azure Portal](https://portal.azure.com)
2. Naviguez vers **Azure Active Directory** > **App registrations**
3. Cliquez sur **New registration**
4. Remplissez:
   - **Name**: `AutoDesk Kiwi Email`
   - **Supported account types**: `Accounts in any organizational directory and personal Microsoft accounts`
   - **Redirect URI**:
     - Type: `Web`
     - URL: `http://localhost:8000/email/outlook/callback`
5. Cliquez sur **Register**

### Étape 2: Obtenir les identifiants

1. Sur la page de votre application, copiez l'**Application (client) ID**
2. Allez dans **Certificates & secrets**
3. Cliquez sur **New client secret**
4. Donnez une description (ex: "AutoDesk Kiwi") et choisissez une expiration
5. Copiez la **Value** du secret (vous ne pourrez plus la voir après!)

### Étape 3: Configurer les permissions

1. Allez dans **API permissions**
2. Cliquez sur **Add a permission**
3. Choisissez **Microsoft Graph**
4. Sélectionnez **Delegated permissions**
5. Ajoutez: `Mail.Read`
6. Cliquez sur **Add permissions**
7. (Optionnel) Cliquez sur **Grant admin consent** si vous êtes admin

### Étape 4: Ajouter à .env

Créez un fichier `.env` dans le dossier `api/` avec:

```env
OUTLOOK_CLIENT_ID=votre-application-client-id
OUTLOOK_CLIENT_SECRET=votre-client-secret
OUTLOOK_TENANT_ID=common
OUTLOOK_REDIRECT_URI=http://localhost:8000/email/outlook/callback
```

## 🔐 Configuration Protonmail

### Étape 1: Obtenir la clé API

1. Connectez-vous à [Protonmail](https://mail.proton.me)
2. Allez dans **Settings** (⚙️)
3. Naviguez vers **Security** > **API Access**
4. Cliquez sur **Generate API Key**
5. Donnez un nom (ex: "AutoDesk Kiwi")
6. Copiez la clé générée

### Étape 2: Ajouter à .env

Ajoutez dans votre fichier `.env`:

```env
PROTONMAIL_API_KEY=votre-cle-api-protonmail
PROTONMAIL_API_URL=https://api.protonmail.ch
```

## 🚀 Utilisation

### 1. Première connexion Outlook

1. Démarrez l'application
2. Allez sur `http://localhost:8000/email/outlook/login`
3. Copiez l'URL retournée et ouvrez-la dans votre navigateur
4. Connectez-vous avec votre compte Microsoft
5. Acceptez les permissions
6. Vous serez redirigé vers la page de callback

### 2. Vérifier les e-mails

- **Outlook**: `http://localhost:8000/email/outlook/unread`
- **Protonmail**: `http://localhost:8000/email/proton/unread`
- **Résumé**: `http://localhost:8000/email/summary`

## ⚠️ Notes importantes

- Les tokens OAuth2 sont stockés en mémoire et seront perdus au redémarrage
- Pour une utilisation en production, utilisez une base de données sécurisée
- Ne partagez jamais vos fichiers `.env` ou vos secrets
- Les clés API Protonmail peuvent avoir des limitations de taux
