# 00 Install Node.js

The setup builds the React site with `npm`, so it needs Node.js 20 or later. The current LTS release works.

## Windows (Chocolatey)

From an administrator PowerShell:

```powershell
choco install nodejs-lts -y
```

## Mac (Homebrew)

```bash
brew install node
```

Without Homebrew, use the LTS installer from [nodejs.org](https://nodejs.org/en/download).

## Check

In a new terminal:

```bash
node --version
npm --version
```

`node --version` should print `v20` or higher.

**Next:** [01 Import and clone](01-import-and-clone.md)
