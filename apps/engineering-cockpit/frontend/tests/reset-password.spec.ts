import { expect, test } from "@playwright/test"
import { randomPassword } from "./utils/random"

test.use({ storageState: { cookies: [], origins: [] } })

test("Password Recovery title is visible", async ({ page }) => {
  await page.goto("/recover-password")

  await expect(
    page.getByRole("heading", { name: "Password Recovery" }),
  ).toBeVisible()
})

test("Input is visible, empty and editable", async ({ page }) => {
  await page.goto("/recover-password")

  await expect(page.getByTestId("email-input")).toBeVisible()
  await expect(page.getByTestId("email-input")).toHaveText("")
  await expect(page.getByTestId("email-input")).toBeEditable()
})

test("Continue button is visible", async ({ page }) => {
  await page.goto("/recover-password")

  await expect(page.getByRole("button", { name: "Continue" })).toBeVisible()
})

// TODO: Fix test and re-enable
// test("User can reset password successfully using the link", async ({
//   page,
//   request,
// }) => {
//   const email = randomEmail()
//   const password = randomPassword()
//   const newPassword = randomPassword()

//   // Create a new user via private API (signup may be disabled)
//   await createUser({ email, password })

//   await page.goto("/recover-password")
//   await page.getByTestId("email-input").fill(email)

//   await page.getByRole("button", { name: "Continue" }).click()

//   const emailData = await findLastEmail({
//     request,
//     filter: (e) => e.recipients.includes(`<${email}>`),
//     timeout: 5000,
//   })

//   const html = await getEmailHtml({ request, emailId: emailData.ID })
//   const resetUrl = extractLink(
//     html,
//     /href="([^"]*\/reset-password\?token=[^"]+)"/,
//   )!
//   const url = new URL(resetUrl)
//   const relativeUrl = `${url.pathname}${url.search}`

//   // Set the new password and confirm it
//   await page.goto(relativeUrl)

//   await page.getByTestId("new-password-input").fill(newPassword)
//   await page.getByTestId("confirm-password-input").fill(newPassword)
//   await page.getByRole("button", { name: "Reset Password" }).click()
//   await expect(page.getByText("Password updated successfully")).toBeVisible()

//   // Check if the user is able to login with the new password
//   await logInUser(page, email, newPassword)
// })

test("Expired or invalid reset link", async ({ page }) => {
  const password = randomPassword()
  const invalidUrl = "/reset-password?token=invalidtoken"

  await page.goto(invalidUrl)

  await page.getByTestId("new-password-input").fill(password)
  await page.getByTestId("confirm-password-input").fill(password)
  await page.getByRole("button", { name: "Reset Password" }).click()

  await expect(page.getByText("Invalid token")).toBeVisible()
})

// TODO: Fix test and re-enable
// test("Weak new password validation", async ({ page, request }) => {
//   const email = randomEmail()
//   const password = randomPassword()
//   const weakPassword = "123"

//   // Create a new user via private API (signup may be disabled)
//   await createUser({ email, password })

//   await page.goto("/recover-password")
//   await page.getByTestId("email-input").fill(email)
//   await page.getByRole("button", { name: "Continue" }).click()

//   const emailData = await findLastEmail({
//     request,
//     filter: (e) => e.recipients.includes(`<${email}>`),
//     timeout: 5000,
//   })

//   const html = await getEmailHtml({ request, emailId: emailData.ID })
//   const resetUrl = extractLink(
//     html,
//     /href="([^"]*\/reset-password\?token=[^"]+)"/,
//   )!
//   const url = new URL(resetUrl)
//   const relativeUrl = `${url.pathname}${url.search}`

//   // Set a weak new password
//   await page.goto(relativeUrl)
//   await page.getByTestId("new-password-input").fill(weakPassword)
//   await page.getByTestId("confirm-password-input").fill(weakPassword)
//   await page.getByRole("button", { name: "Reset Password" }).click()

//   await expect(
//     page.getByText("Password must be at least 8 characters"),
//   ).toBeVisible()
// })
