import twitter, time, sys, json, base64, re, string, os.path, math,traceback

#consumer key
CK=""
#consumer secret
CS=""
#access token
AT=""
#access token secret
ATS=""
#bot screen name
BSN="@base64bot"
#mentionidfile
MFILE="mentionID.txt"

def encodeB64(editText):
    return base64.b64encode(editText)

def tweetIt(encodedResult, mentionName, mentionID):
    #so, is the result smaller than 140 chars?
    #if so, we can just tweet back
    if mentionName == "soot":
        encodedResult = "Sorry Dave, I can't do that."
    tweetString = "@" + mentionName + " " + encodedResult
    if len(tweetString) < 140:
        twitResult=api.PostUpdates(tweetString, in_reply_to_status_id=mentionID)
    else:
        print("we need to split this up in bits of 140 chars")
        #the extra chars are
        # @[mentionname]{space}x/y{space}
        maxTweetLen = 140-(len(mentionName)+6)
        howManyTweets = int(math.ceil(len(encodedResult)/float(maxTweetLen)))
        tweetNum=1
	#ok so maximum amount of chars we can fit into one message is maxTweetLen
        #lets do some formating magic, to get all the tweets out
        while len(encodedResult) > 1:
            tmpTweetStr = encodedResult[0:maxTweetLen]
            encodedResult=encodedResult[maxTweetLen:len(encodedResult)]      
            tweetStr = "@%s %i/%i %s" % (mentionName,tweetNum,howManyTweets,tmpTweetStr)
            twitResult=api.PostUpdates(tweetStr, in_reply_to_status_id=mentionID)
            tweetNum+=1
    return

def workWithValid(decodeResult, mentionName, mentionID):
    printable = set(decodeResult).issubset(string.printable)
    if printable:
        print ("valid printable lets tweet")
        tweetIt(decodeResult,mentionName,mentionID)
    else:
        print ("not valid base64, so lets encode")
        encodedResult = encodeB64(decodeResult)
        tweetIt(encodedResult, mentionName,mentionID)
    return

def do_auth():
    #lets auth
    print ("Authenticating...")
    api = twitter.Api(consumer_key=CK, consumer_secret=CS, access_token_key=AT, access_token_secret=ATS)
    api.SetUserAgent("Base64bot agent")
    api.SetXTwitterHeaders("Base64Bot","https://tldr.nu","1")
    print ("Done, lets start working")
    return api

def getSinceID():
    sinceID=0
    if os.path.isfile(MFILE):
        print("file for least ID exists")
        with open(MFILE) as f:
            sinceID=int(f.read())
            f.close()
    return sinceID

if __name__ == "__main__":
    api=do_auth()
#lets wait for mentions
#first, lets see if file MFILE exists
    sinceID=getSinceID()

    while True:
        #first, lets read what the last tweet was we responded to
        #thats the since_id
        #now lets get the new mentions, per 20
        mentions=""
        print ("Getting mentions")
        try:
            mentions = api.GetMentions(5,sinceID,None,False,False,False)
        except:
            #bugger, prolly a timeout
            traceback.print_exc()
            time.sleep(60)
        if len(mentions)> 0:
            print("we got mentions!")
            for item in mentions:
                mentionData=json.loads(str(item))
                #print mentionData
                mentionName=mentionData['user']['name']
                mentionText=mentionData['text']
                mentionID=mentionData['id'] #we need this to update since_id lateron
                print ("who tweeted us: %s " % mentionName)
                print ("what was tweeted: %s " % mentionText)
                print ("messageid is: %s" % mentionID)
                #ok so lets handle what was tweeted at us
	        #format requires it starts with our own name
                if mentionText.startswith(BSN):
                    print ("alright, we need to do something with this!")
	    	#first, lets fix the text
                    editText = mentionText.replace(BSN+" ","")
 
                #So, is this a base64 string?
                #this is not foolproof, thats why workWithValid
    		#requires an extra test to see if it really is base64 or not
                    try: 
                        decodeResult = base64.decodestring(editText)
                        print("seems valid base64, lets try decode")
                        workWithValid(decodeResult, mentionName, mentionID)
                    except: #not valid base64, so lets encode
                        traceback.print_exc()
                        print ("seems invalid, lets try encode instead")
                        encodedResult = encodeB64(editText)
                        tweetIt(encodedResult, mentionName, mentionID)
                
                #alright, it went all fine, lets update the since_id
                    sinceID=mentionID
                #aand write it to the file
                    with open(MFILE, 'w') as f:
                        f.write(str(sinceID))
                        f.close()
                    print("ID written to file")		
        else:
            print("No new mentions :< Lets wait and try again.")
        print("short pause")
        time.sleep(60)
