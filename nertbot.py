import cv2
import numpy as np
from imutils import contours as imcontours
import pytesseract
# Comment out the following line if running on linux
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\Tesseract.exe'
from matplotlib import pyplot as plt
import io

red = (0, 0, 255)
green = (0, 255, 0)
blue = (255, 0, 0)
orange = (0, 127, 255)

class Player:
    def __init__(self, nameContour, scoreFrames, nertFrames, nertRounds):
        self.nameContour = nameContour
        self.scoreFrames = scoreFrames
        self.nertFrames = nertFrames
        self.nertRounds = nertRounds
        self.name = ""
        self.scores = []
        self.cumScore = []


def within(A, B, T):
    # Checks if A and B are within a tolerance T
    return (abs(A-B) <= T)

def similarColor(pixel, color, threshold):
    # Checks if a pixel is similar to a defined color
    isSimilar = True
    for i in range(0,len(pixel)-1):
        if not within(pixel[i], color[i], threshold):
            isSimilar = False
    return isSimilar

def isIn(A, B):
    #Checks in contour A is fully contained within contour B
    xA,yA,wA,hA = cv2.boundingRect(A)
    xB,yB,wB,hB = cv2.boundingRect(B)
    return (xA > xB) and (yA > yB) and (xA+wA < xB+wB) and (yA+hA < yB+hB)# and (wA < wB) and (hA < hB)

def borders(A, B, T):
    # Checks if the left border of A overlaps the right border of B
    xA,yA,wA,hA = cv2.boundingRect(A)
    xB,yB,wB,hB = cv2.boundingRect(B)
    xB2 = xB+wB
    return within(xA,xB2,T) and within(yA,yB,T)

def findScoreboard(image):
    # Locates the Nerts scoreboard and returns a cropped image
    scoreboardColor = [49,42,19]
    blur = cv2.GaussianBlur(image, (5,5), 0)
    h,w,c = image.shape
    xMin = w
    xMax = 0
    yMin = h
    yMax = 0
    # Find the four corners by color
    for y in range(0,h):
        for x in range(0,w):
            if similarColor(blur[y,x], scoreboardColor, 1):
                if x < xMin:
                    xMin = x
                if x > xMax:
                    xMax = x
                if y < yMin:
                    yMin = y
                if y > yMax:
                    yMax = y
    return(image[yMin:yMax, xMin:xMax])

def getContours(original, thresh, imageArea):
    cuttoffFactor = 2074
    c = 0
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    squares = []
    users = []
    otherContours = []
    for i in contours:
        area = cv2.contourArea(i)
        x,y,w,h = cv2.boundingRect(i)
        if area > imageArea/cuttoffFactor:
            # the contour is big enough for us to care about
            if within(w, h, 5):
                # we have a square
                squares.append(i)
                #cv2.drawContours(original, contours, c, (0, 255, 0), 3)
            else:
                otherContours.append(i)
        c+=1
    scoreFrames = []
    nertFrames = []
    for square in squares:
        isNertFrame = False
        for check in squares:
            if isIn(square, check):
                isNertFrame = True
        if isNertFrame:
            nertFrames.append(square)
        else:
            scoreFrames.append(square)
    nRows = 6
    nCols = int(len(scoreFrames)/nRows)
    # Sort all the score frames
    # https://stackoverflow.com/questions/59182827/how-to-get-the-cells-of-a-sudoku-grid-with-opencv
    (cnts, _) = imcontours.sort_contours(scoreFrames, method="top-to-bottom")
    rows = []
    row = []
    for (i, c) in enumerate(cnts, 1):
        area = cv2.contourArea(c)
        row.append(c)
        if i % nCols == 0:  
            (cnts, _) = imcontours.sort_contours(row, method="left-to-right")
            rows.append(cnts)
            row = []

    names = []
    for row in rows:
        firstFrame = row[0]
        for i in otherContours:
            #print((firstFrame, i))
            if borders(firstFrame, i, 10):
                names.append(i)

    players = []
    for i in range(0, len(names)):
        playerNertRounds = []
        playerNertFrames = []
        for j in range(0, len(rows[i])):
            for nertFrame in nertFrames:
                if isIn(nertFrame, rows[i][j]):
                    playerNertRounds.append(j)
                    playerNertFrames.append(nertFrame)
        player = Player(names[i], rows[i], playerNertFrames, playerNertRounds)
        players.append(player)

    cv2.drawContours(original, nertFrames, -1, green, 2)
    #cv2.drawContours(original, otherContours, -1, orange, 2)
    cv2.drawContours(original, rows[0], -1, (255, 0, 40), 2)
    cv2.drawContours(original, [names[0]], -1, (255, 0, 40), 2)
    cv2.drawContours(original, rows[1], -1, (255, 0, 80), 2)
    cv2.drawContours(original, [names[1]], -1, (255, 0, 80), 2)
    cv2.drawContours(original, rows[2], -1, (255, 0, 120), 2)
    cv2.drawContours(original, [names[2]], -1, (255, 0, 120), 2)
    cv2.drawContours(original, rows[3], -1, (255, 0, 160), 2)
    cv2.drawContours(original, [names[3]], -1, (255, 0, 160), 2)
    cv2.drawContours(original, rows[4], -1, (255, 0, 200), 2)
    cv2.drawContours(original, [names[4]], -1, (255, 0, 200), 2)
    cv2.drawContours(original, rows[5], -1, (255, 0, 240), 2)
    cv2.drawContours(original, [names[5]], -1, (255, 0, 240), 2)

    return original, players

def getSlice(image, contour):
    x,y,w,h = cv2.boundingRect(contour)
    return image[y:y+h,x:x+w]

def zoom(image, pct):
    h,w = image.shape
    return image[int(h*pct):int(h-h*pct), int(w*pct):int(w-w*pct)]

def parseData(image, players):
    # First, lets parse the names
    for player in players:
        nameSlice = getSlice(image, player.nameContour)
        name = pytesseract.image_to_string(nameSlice)
        nameSplit = name.split()
        if len(nameSplit) > 1:
            player.name = name.split()[1]
        else:
            # If the name is blank, remove the player
            players.remove(player)
    # Restart the loop since we may have removed players
    for player in players:
        scores = []
        for i in range(0, len(player.scoreFrames)):#scoreFrame in player.scoreFrames:
            scoreFrame = player.scoreFrames[i]
            if i in player.nertRounds:
                ind = player.nertRounds.index(i)
                scoreSlice = getSlice(image, player.nertFrames[ind])
                scoreSlice = zoom(scoreSlice, .15)
            else:
                scoreSlice = getSlice(image, scoreFrame)
            config = ('-l eng --oem 0 --psm 7')
            score = pytesseract.image_to_string(scoreSlice, config=config)
            score = score.strip()
            score = score.replace("I", "1")
            score = score.replace("B", "8")
            score = score.replace(".", "9")
            if score != "":
                try:
                    score = int(score)
                except:
                    cv2.imshow(score, scoreSlice)
                    print(score)
                    score = 0
                scores.append(score)
            player.scores = scores
    return players

def calcScores(players):
    for player in players:
        cumScore = [0]
        for i in range(len(player.scores)):
            cumScore.append(cumScore[i]+player.scores[i])
        player.cumScore = cumScore
    return players

def drawPlot(players):
    #with plt.xkcd():
    fig, ax = plt.subplots()
    for player in players:
        ax.plot(player.cumScore, label=player.name)
    ax.set(title="nert", xlabel="Round", ylabel="Score")
    ax.legend()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf
    #plt.show()


def processScreenshot(image):
    h,w,c = image.shape
    scoreboard = findScoreboard(image)
    gray = cv2.cvtColor(scoreboard, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    nop,thresh = cv2.threshold(gray,50,255,cv2.THRESH_BINARY_INV)
    contoured, players = getContours(scoreboard, thresh, h*w)
    players = parseData(thresh, players)
    players = calcScores(players)
    plotBuffer = drawPlot(players)
    #cv2.imshow('image', contoured)
    #cv2.waitKey(0)
    return plotBuffer

if __name__ == "__main__":
    image = cv2.imread("samples/nert0.png")
    processScreenshot(image)
    
