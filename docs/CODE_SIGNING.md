# 🔏 Code Signing for HiveOS

> Signing your HiveOS executables with an Authenticode certificate removes "Windows protected your PC" / "Unknown publisher" warnings when users download and run HiveOS.

## Prerequisites

- An **Extended Validation (EV) Code Signing Certificate** or **Organization Validated (OV) Certificate**
  - Popular issuers: DigiCert, Sectigo, GlobalSign, Let's Encrypt (Code Signing only)
  - Cost: ~$200–$600/year for OV, ~$300–$500/year for EV
  - EV certs use a hardware token (USB dongle); OV certs can be stored in Azure Key Vault or CI secrets

## How Signing Works

The build pipeline produces:
1. `dist/HiveOS/HiveOS.exe` — the main executable (PyInstaller-built, one-dir)
2. `dist/HiveOS-Setup-v0.X.X.exe` — the Inno Setup installer (MSI)

Both files should be Authenticode-signed before release.

## Option 1: Azure Key Vault (CI-friendly, no hardware token)

```yaml
# Add to .github/workflows/release.yml after Verify / before Upload

- name: Sign executables with Azure Key Vault
  uses: azure/azure-code-signing-action@v1
  with:
    azure-signing-client-id: ${{ secrets.AZURE_SIGNING_CLIENT_ID }}
    azure-signing-tenant-id: ${{ secrets.AZURE_SIGNING_TENANT_ID }}
    azure-signing-client-secret: ${{ secrets.AZURE_SIGNING_CLIENT_SECRET }}
    azure-signing-key-vault-url: ${{ secrets.AZURE_KEY_VAULT_URL }}
    azure-signing-key-name: ${{ secrets.AZURE_SIGNING_KEY_NAME }}
    files: |
      dist/HiveOS/HiveOS.exe
      dist/HiveOS-Setup-*.exe
```

## Option 2: Windows `signtool` with local certificate

```powershell
# Install cert locally (one-time), then sign:
$cert = Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert
signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 `
  dist\HiveOS\HiveOS.exe
signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 `
  dist\HiveOS-Setup-v*.exe

# Verify:
signtool verify /pa dist\HiveOS\HiveOS.exe
```

## Option 3: GitHub Actions Marketplace

```yaml
- name: Sign with code-signing-action
  uses: nick-invision/code-signing-action@v1
  with:
    certificate-file: ${{ secrets.CODESIGN_CERT_BASE64 }}
    certificate-password: ${{ secrets.CODESIGN_CERT_PASSWORD }}
    files: |
      dist/HiveOS/HiveOS.exe
      dist/HiveOS-Setup-*.exe
```

## Self-Signed (for testing only)

```powershell
# Create self-signed cert (DO NOT use for production — users will still see warnings)
New-SelfSignedCertificate -Type Custom -Subject "CN=HiveOS" `
  -KeyUsage DigitalSignature -FriendlyName "HiveOS Test Signing" `
  -CertStoreLocation "Cert:\CurrentUser\My" -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3")

# Export to .pfx
$pwd = ConvertTo-SecureString -String "test123" -Force -AsPlainText
Export-PfxCertificate -Cert "Cert:\CurrentUser\My\<THUMBPRINT>" `
  -FilePath build\hiveos-test.pfx -Password $pwd

# Sign
signtool sign /fd SHA256 /a /f build\hiveos-test.pfx /p test123 `
  dist\HiveOS\HiveOS.exe
```

> [!NOTE]
> Self-signed certs still trigger "Unknown publisher" on other machines. Only use for local testing.

## How to Add to CI Pipeline

Once you have a certificate, uncomment the signing step in `.github/workflows/release.yml`
and add the relevant secrets to your GitHub repository settings:

1. Go to Settings → Secrets and variables → Actions
2. Add your signing secrets (certificate, password, or Azure credentials)
3. Uncomment the signing step in `release.yml`
4. Push a new tag — the pipeline builds, signs, and publishes

## Verifying a Signed Build

```powershell
# Check digital signature
signtool verify /pa dist\HiveOS\HiveOS.exe

# View certificate details
Get-AuthenticodeSignature dist\HiveOS\HiveOS.exe | Format-List

# Check in File Explorer: right-click → Properties → Digital Signatures
```
