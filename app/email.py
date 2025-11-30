"""Email utilities"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from .config import settings


async def send_email(to: str, subject: str, body: str):
    """Send email"""
    message = MIMEMultipart("alternative")
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject

    html_part = MIMEText(body, "html")
    message.attach(html_part)

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=settings.SMTP_TLS,
    )


async def send_verification_email(email: str, token: str):
    """Send verification email"""
    verification_url = f"https://arkana.avila.inc/verify?token={token}"

    template = Template("""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .button {
                display: inline-block;
                padding: 12px 24px;
                background: #00d4ff;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
            .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔐 Verifique seu email</h2>
            <p>Obrigado por se registrar no {{ app_name }}!</p>
            <p>Clique no botão abaixo para verificar seu endereço de email:</p>
            <p><a href="{{ verification_url }}" class="button">Verificar Email</a></p>
            <p>Ou copie e cole este link no seu navegador:</p>
            <p><code>{{ verification_url }}</code></p>
            <div class="footer">
                <p>Se você não criou esta conta, ignore este email.</p>
                <p>© 2025 Ávila Inc. Todos os direitos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """)

    body = template.render(
        app_name=settings.APP_NAME,
        verification_url=verification_url
    )

    await send_email(email, f"Verifique seu email - {settings.APP_NAME}", body)


async def send_password_reset_email(email: str, token: str):
    """Send password reset email"""
    reset_url = f"https://arkana.avila.inc/reset-password?token={token}"

    template = Template("""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .button {
                display: inline-block;
                padding: 12px 24px;
                background: #ff4444;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
            .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔒 Redefinição de Senha</h2>
            <p>Você solicitou a redefinição de senha para {{ app_name }}.</p>
            <p>Clique no botão abaixo para redefinir sua senha:</p>
            <p><a href="{{ reset_url }}" class="button">Redefinir Senha</a></p>
            <p>Ou copie e cole este link no seu navegador:</p>
            <p><code>{{ reset_url }}</code></p>
            <p><strong>Este link expira em 1 hora.</strong></p>
            <div class="footer">
                <p>Se você não solicitou esta redefinição, ignore este email.</p>
                <p>© 2025 Ávila Inc. Todos os direitos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """)

    body = template.render(
        app_name=settings.APP_NAME,
        reset_url=reset_url
    )

    await send_email(email, f"Redefinição de Senha - {settings.APP_NAME}", body)
