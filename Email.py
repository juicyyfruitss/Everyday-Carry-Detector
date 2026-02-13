from postmarker.core import PostmarkClient
import database

postmark = PostmarkClient(server_token = "d7499ce1-f3d0-4f2b-aa85-1ca332eb1e8c")

senderemail = "dlr060@email.latech.edu"
DB = database.DB()
user = DB.GetCurrentUser()
useremail = user

postmark.emails.send(
From = senderemail,
To = useremail,
Subject = "Item left behind",
HtmlBody="<strong>This is a test email sent via Postmark + Python!</strong>",
TextBody = "Hello World"
)

