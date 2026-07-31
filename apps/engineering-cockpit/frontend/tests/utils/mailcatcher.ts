import type { APIRequestContext } from "@playwright/test"

type Email = {
  ID: string
  id?: number
  recipients: string[]
  To?: Array<{ Address: string }>
  subject: string
  Subject?: string
}

function getMailcatcherBaseUrl(): string {
  const configuredHost = process.env.MAILCATCHER_HOST || "http://127.0.0.1:8025"

  try {
    const url = new URL(configuredHost)
    if (url.hostname === "localhost") {
      url.hostname = "127.0.0.1"
    }
    return url.toString().replace(/\/$/, "")
  } catch {
    return configuredHost
      .replace("http://localhost", "http://127.0.0.1")
      .replace(/\/$/, "")
  }
}

async function findEmail({
  request,
  filter,
}: {
  request: APIRequestContext
  filter?: (email: Email) => boolean
}) {
  const response = await request.get(
    `${getMailcatcherBaseUrl()}/api/v1/messages`,
  )

  if (!response.ok()) {
    throw new Error(
      `Mailcatcher API request failed with status ${response.status()}: ${await response.text()}`,
    )
  }

  const data = await response.json()

  // Handle both mailpit and old mailcatcher response formats
  const rawEmails = Array.isArray(data) ? data : data.messages || []

  // Normalize all emails first
  const emails = rawEmails.map((email: any) => {
    const recipients =
      email.To?.map((t: any) => `<${t.Address}>`) || email.recipients || []
    return {
      ID: email.ID || email.id,
      id: email.id || email.ID,
      recipients,
      subject: email.Subject || email.subject || "",
    }
  })

  // Then apply filter to normalized emails
  const filtered = filter ? emails.filter(filter) : emails

  const email = filtered[filtered.length - 1]

  return email || null
}

export function findLastEmail({
  request,
  filter,
  timeout = 5000,
}: {
  request: APIRequestContext
  filter?: (email: Email) => boolean
  timeout?: number
}) {
  const timeoutPromise = new Promise<never>((_, reject) =>
    setTimeout(
      () => reject(new Error("Timeout while trying to get latest email")),
      timeout,
    ),
  )

  const checkEmails = async () => {
    while (true) {
      const emailData = await findEmail({ request, filter })

      if (emailData) {
        return emailData
      }
      // Wait for 100ms before checking again
      await new Promise((resolve) => setTimeout(resolve, 100))
    }
  }

  return Promise.race([timeoutPromise, checkEmails()])
}

export async function getEmailHtml({
  request,
  emailId,
}: {
  request: APIRequestContext
  emailId: string
}): Promise<string> {
  const response = await request.get(
    `${getMailcatcherBaseUrl()}/api/v1/message/${emailId}`,
  )
  if (!response.ok()) {
    throw new Error(
      `Failed to fetch email ${emailId}: ${response.status()} ${await response.text()}`,
    )
  }
  const data = await response.json()
  return data.HTML || data.Text || ""
}

export function extractLink(html: string, pattern: RegExp): string | null {
  const match = html.match(pattern)
  return match ? match[1] || match[0] : null
}
