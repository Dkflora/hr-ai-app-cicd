# 00 Install Node.js

The setup builds the chatbot's web page with a tool called `npm`. `npm` comes with Node.js, so you need Node.js version 20 or later. The current LTS (long-term support) release works.

## Windows (Chocolatey)

Open PowerShell as an administrator: right-click **PowerShell** and choose **Run as administrator**. Then run:

```powershell
choco install nodejs-lts -y
```

This is the only PowerShell command in the lab. Every other command is written for **Git Bash**, which comes with Git for Windows.

## Mac (Homebrew)

```bash
brew install node
```

If you do not have Homebrew, download the LTS installer from [nodejs.org](https://nodejs.org/en/download) and run it.

## Check

Open a new terminal (Git Bash on Windows, Terminal on a Mac), then run:

```bash
node --version
npm --version
```

`node --version` should print `v20` or higher. `npm --version` prints a version number too.

**Next:** [01 Import and clone](01-import-and-clone.md)
