from twilio.rest import TwilioRestClient
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import feedHandler
import smtplib
import sys
import os

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def location(file):
    return os.path.join(__location__,file)

##Setting up variables
if(len(sys.argv) > 2):
    rssfeed = sys.argv[1]+","+sys.argv[2]
    open(location('rss.txt'), 'a').write(rssfeed+'\n')

if not os.path.exists(location('rss.txt')):
    print "Pass an RSS feed and a name for that feed as two separate arguments; Exiting."
    sys.exit()


def checkAccountData():
    if not os.path.exists(location('accountData.txt')):
        accountData = open(location('accountData.txt'), 'w')
        if int(raw_input('Which way would you like to receive notifications?:\n\t[0] Twilio\n\t[1] Gmail\n')):
            print "You've selected 'Gmail'"
            accountData.write('GMAIL\n')
            accountData.write(raw_input('Gmail user (user_name@gmail.com): ') + '\n')
            accountData.write(raw_input('Gmail password: ') + '\n')
        else:
            print "You've selected 'Twilio'"
            accountData.write('TWILIO\n')
            accountData.write(raw_input('Twilio ACCOUNT_SID: ') + '\n')
            accountData.write(raw_input('Twilio AUTH_TOKEN: ') + '\n')
            accountData.write(raw_input('Twilio Phone Number (+19876543210): ') + '\n')
            accountData.write(raw_input('Receiving Phone Number (+19876543210): ') + '\n')
            accountData.close()

def getAccountData():
    accountData = {}
    accountFile = open(location('accountData.txt'), 'r')
    sendType = accountFile.readline().rstrip()
    if sendType == "GMAIL":
        accountData['sendMethod'] = 'GMAIL'
        accountData['GMAIL_USER'] = accountFile.readline().rstrip()
        accountData['GMAIL_PSWD'] = accountFile.readline().rstrip()

    elif sendType == "TWILIO":
        accountData['sendMethod'] = "TWILIO"
        accountData['ACCOUNT_SID'] = accountFile.readline().rstrip()
        accountData['AUTH_TOKEN'] = accountFile.readline().rstrip()
        accountData['phoneSender'] = accountFile.readline().rstrip()
        accountData['phoneReciver'] = accountFile.readline().rstrip()

    return accountData

def sendEmail(feed, accountData):
    # print feed
    data = feed.formatEmail()
    if data['body']:
        FROM = accountData['GMAIL_USER']
        TO = accountData['GMAIL_USER']
        MESSAGE = MIMEMultipart('alternative')
        MESSAGE['subject'] = data['subject']
        MESSAGE['From'] = FROM
        MESSAGE['To'] = TO
        MESSAGE.preamble = data['body']
        MESSAGE.attach(MIMEText(data['body'], 'html'))
        # Attempt to send email
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
            server.ehlo()
            server.starttls()
            server.login(accountData['GMAIL_USER'], accountData['GMAIL_PSWD'])
            server.sendmail(FROM, TO, MESSAGE.as_string())
            server.close()
            print 'Successfully sent email'
        except Exception as e:
            print "Failed to send mail"
            print e


def sendSMS(feed, accountData):
    ACCOUNT_SID = accountData['ACCOUNT_SID']
    AUTH_TOKEN = accountData['AUTH_TOKEN']
    phoneSender = accountData['phoneSender']
    phoneReciver = accountData['phoneReciver']

    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)    

    text = feed.formatSMS()

    ##If the string is blank send it along
    if text is not "":
        client.messages.create(
            from_= phoneSender, to = phoneReciver, body = text
        )



def writeOldEntries(feeds):
    entriesFile = open(location('entries.txt'), 'w')

    for feed in feeds:
        entriesFile.write(feed.buildEntryLine())

def main():

    checkAccountData()
    transmitDict = {}
    transmitDict['GMAIL'] = sendEmail
    transmitDict['TWILIO'] = sendSMS

    feeds = feedHandler.buildFeeds()

    accountData = getAccountData()
    # sendFunc is a function that we get out of the transmit dict. By doing
    # this, it means not much code is required to add other ways of sending
    # information.
    sendFunc = transmitDict[accountData['sendMethod']]

    for x in feeds:
        sendFunc(x, accountData)

    writeOldEntries(feeds)


if __name__ == '__main__':
    main()

