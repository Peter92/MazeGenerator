import pymel.core as py
import random as rd
import operator
import codeStuff
reload( codeStuff )
from time import time
from decimal import Decimal
global indent
global minimumTimeToOutput
global iterationsPoints
global iterationsCubes
global iterationsCurves
global iterationsColour
indent = "  "
'''
To do:
    Get group location and append to object location
    py.defaultNavigation( source = shaderSelect, destination = cubeSelect, connectToExisting = True )
    py.currentTime( 1, edit = True, update = True )
    
    Smooth size reduction
    0 = 0
    0.5 = 25%
    0.75 = 50%
    1 = 100%
'''

#Main
forkLength = 100
forkAmount = 100
numDimensions = 3
nearestNeighbourSearch = False
scaleAmount = 10
#Extra
plotCurves = False
plotCubes = False
drawShaders = False
cubeScale = 0.9
reduceInSize = True
reduceRootAmount = 0.713
locationPrecision = 3
noiseAmount = 0.1

maxAttemptsAtNewDirection = numDimensions*2-1
#Fix for non matching fork amount + length
#[under construction]
'''
if forkLength > forkAmount:
    reduceRootAmount += 0.02 * float( forkLength )**0.925/float( forkAmount )
elif forkLength < forkAmount:
    reduceRootAmount -= 0.02 * float( forkAmount )**0.925/float( forkLength )
float( forkAmount )/float( forkLength )
'''
#Output
timeIncrement = 0.75
iterationsPoints = 10
iterationsCurves = 1
iterationsCubes = 5
iterationsColour = 3
minimumTimeToOutput = 0.2

'''
#Artistic paving stones:
forkLength = 50
forkAmount = 50
numDimensions = 2
nearestNeighbourSearch = False
'''

#Store other information
#codeStuff.InfoStore( "reduceSizeExponential" ).set( reduceSizeExponential, True )



#Remove any non existant groups
def cleanOldGenerations():
    
    #Read from store
    allGenerations = codeStuff.InfoStore( "allGenerations" ).read()
    remainingGenerations = []
    
    #Test each group
    for i in range( len( allGenerations ) ):
        try:
            py.ls( str( allGenerations[i] ) + "GenGroup" )[0]
            remainingGenerations.append( allGenerations[i] )
        except:
            pass
    
    #Update list with all valid groups
    codeStuff.InfoStore( "allGenerations" ).set( remainingGenerations )
    
    #Output message
    numCleanedGenerations = len( allGenerations ) - len( remainingGenerations )  
    if numCleanedGenerations != 0:
        extraS = ""
        if numCleanedGenerations != 1:
            extraS = "s"
        print str( numCleanedGenerations ) + " generation record" + extraS + " cleaned from store"
        
    return numCleanedGenerations

#Draw cubes
def drawCubes( letter ):
    cubeSize = scaleAmount * cubeScale
    sortedListOfPoints = sortByFork( codeStuff.InfoStore( "PointList", letter.lower() + "GenGroup" ).read(), codeStuff.InfoStore( "StartingForks", letter.lower() + "GenGroup" ).read() )
    reduceInSize = py.getAttr( letter.lower() + "GenGroup.ReduceSize" )
    #Abort if invalid
    if len( sortedListOfPoints ) == 0:
        print "Cannot generate cubes"
        return
    else:
        #Remove existing list of cubes
        try:
            py.delete( letter.lower() + "Cubes" )
        except:
            pass
        #Recreate group
        cubeGroup = py.group( n = letter.lower() + 'Cubes', empty = True )
        codeStuff.InfoStore( "CubeList", letter.lower() + "Cubes" ).set([])
        py.parent( cubeGroup, letter.lower() + "GenGroup" )
        #Delete cubes if the group hasn't deleted
        existingList = codeStuff.InfoStore( "CubeList", letter.lower() + "Cubes" ).read()
        if len( existingList ) > 0:
            print "Removing existing cubes..."
            for i in range( len( existingList ) ):
                try:
                    py.delete( existingList[i] )
                except:
                    pass
    print "Generating cubes..."
    highestSequence = py.getAttr( letter.lower() + "GenGroup.HighestSequence" )
    maxCubes = float( len( codeStuff.InfoStore( "PointList", letter.lower() + "GenGroup" ).read() ) )
    startCubeTime = time()
    totalCubes = 0
    nextTime = startCubeTime + timeIncrement
    listOfCubes = []
    for forkNumber in sortedListOfPoints:
    #Draw cube
        curbeList = []
        for i in range( len( sortedListOfPoints[forkNumber] ) ):
            #Get info
            coordinates = sortedListOfPoints[forkNumber][i][0]
            sequenceNumber = sortedListOfPoints[forkNumber][i][1]
            colourNumber = sortedListOfPoints[forkNumber][i][2]
            if highestSequence > 0:
                percentComplete = sequenceNumber/highestSequence
            else:
                percentComplete = 0
            #Create cube
            newCube = py.polyCube( n = letter.lower() + "Cube", width = cubeSize, depth = cubeSize, height = cubeSize )[0]
            py.move( newCube, coordinates )
            py.parent( newCube, letter.lower() + "Cubes" )
            listOfCubes.append( str( newCube ) )
            #Store colour value inside cube
            py.addAttr( newCube, longName = "ColourValue" )
            py.setAttr( newCube + ".ColourValue", colourNumber )
            #Scale cube based on colour value
            if reduceInSize == True:
                py.scale( newCube, colourNumber, colourNumber, colourNumber )
            if totalCubes % iterationsCubes == 0:
                if time() > nextTime:                  
                    nextTime = time() + timeIncrement
                    percentage = totalCubes / maxCubes
                    if percentage > 100:
                        print totalCubes
                        print maxCubes
                    print indent + str( totalCubes ) + " cubes generated (" + str( round( 100*percentage, 2 ) ) + "%)"
                    codeStuff.UpdateViewport()
            totalCubes += 1
            
    print objectsPerSecond( startCubeTime, "cubes", totalCubes )
    
    startStoreTime = time()
    print "Storing cube information..."
    codeStuff.UpdateViewport()
    codeStuff.InfoStore( "CubeList", letter.lower() + "Cubes" ).set( listOfCubes )
    if time() - startStoreTime > minimumTimeToOutput:
        print "Stored in " + str( codeStuff.TimeOutput( startStoreTime, time() ) )

#Draw curves
def drawCurves( letter ):
    letter = str( letter )
    sortedListOfPoints = sortByFork( codeStuff.InfoStore( "PointList", letter.lower() + "GenGroup" ).read(), codeStuff.InfoStore( "StartingForks", letter.lower() + "GenGroup" ).read() )
    #Abort if invalid
    if len( sortedListOfPoints ) == 0:
        print "Cannot generate curves"
        return
    else:
        #Remove existing list of curves
        try:
            py.delete( letter.lower() + "Curves" )
        except:
            pass
        #Recreate group
        curveGroup = py.group( n = letter.lower() + 'Curves', empty = True )
        py.parent( curveGroup, letter.lower() + "GenGroup" )
        codeStuff.InfoStore( "CurveList", letter.lower() + "Curves" ).set([])
        #Delete curves if the group hasn't deleted
        existingList = codeStuff.InfoStore( "CurveList", letter.lower() + "Curves" ).read()
        if len( existingList ) > 0:
            print "Removing existing curves..."
            existingList.append( letter.lower() + "Curves" )
            for i in range( len( existingList ) ):
                try:
                    py.delete( existingList[i] )
                except:
                    pass
    print "Generating curves..."
    totalCurves = 0
    startDrawCurveTime = time()
    nextTime = startDrawCurveTime + timeIncrement
    listOfCurves = []
    for forkNumber in sortedListOfPoints:
        #Draw curve
        curveList = []
        for i in range( len( sortedListOfPoints[forkNumber] ) ):
            #ConvertTo3D
            curveListTemp = []
            skipAmount = 0
            for j in range( 3 ):
                #For 1D generations
                if j != 2 and numDimensions == 1:
                    curveListTemp.append( 0 )
                    skipAmount += 1
                #For 2D generations
                elif j == 2 and numDimensions == 2:
                    curveListTemp.append( 0 )
                    skipAmount += 1
                else:
                    k = j - skipAmount
                    #Store value
                    curveListTemp.append( sortedListOfPoints[forkNumber][i][0][k] )
            curveList.append( curveListTemp )
        if len( curveList ) > 1:
            newCurve = py.curve( n = letter.lower() + "Curve", p = curveList, d = 1 )
            py.parent( newCurve, letter.lower() + "Curves" )
            listOfCurves.append( str( newCurve ) )
            totalCurves += 1
            #Output message
            if totalCurves % iterationsCurves == 0:
                if time() > nextTime:
                    nextTime = time() + timeIncrement
                    percentage = 100.0*totalCurves/sortedListOfPoints.keys()[-1]
                    print indent + str( totalCurves ) + " curves generated (" + str( round( percentage, 2 ) ) + "%)"
                    codeStuff.UpdateViewport()
                    
    print objectsPerSecond( startDrawCurveTime, "curves", totalCurves )
    
    startStoreTime = time()
    print "Storing curve information..."
    codeStuff.UpdateViewport()
    codeStuff.InfoStore( "CurveList", letter.lower() + "Curves" ).set( listOfCurves )
    if time() - startStoreTime > minimumTimeToOutput:
        print "Stored in " + str( codeStuff.TimeOutput( startStoreTime, time() ) )

def objectsPerSecond( startTime, objectName, totalObjects ):
    if time()-startTime > 1:
        generationsPerSecond = totalObjects/( time()-startTime )
    else:
        generationsPerSecond = totalObjects
    return str( totalObjects ) + " " + str( objectName ) + " generated in " + str( codeStuff.TimeOutput( startTime, time() ) ) + " (" + str( round( generationsPerSecond, 2 ) ) + " per second)"
    
def sortByFork( listOfPoints, listOfStartingForks ):
    #Sort dictionary by the fork number
    print "Sorting values..."
    try: 
        sortedByFork = sorted(listOfPoints.items(), key=operator.itemgetter(1))
    except:
        print "Invalid list of points"
        return None
    startSortTime = time()
    sortedListOfPoints = {}
    sortedBySequenceNumber = {}
    for i in range( len( sortedByFork ) ):
        forkNumber = sortedByFork[i][1][0]
        #Include any extra values here
        extraValues = [sortedByFork[i][0]]
        for j in range( 1, len( sortedByFork[i][1] ) ):
            extraValues.append( sortedByFork[i][1][j] )
        #Append to dictionary or create new one
        try:
            sortedListOfPoints[forkNumber].append( extraValues )
        except:
            sortedListOfPoints[forkNumber] = [ extraValues ]
    for forkNumber in sortedListOfPoints:
        #Use the fork it originated from to get the initial point
        startingFork = listOfStartingForks[forkNumber]
        if startingFork >= 0:
            startingSequenceNumber = sortedListOfPoints[forkNumber][0][1]-1
            for i in range( len( sortedListOfPoints[ startingFork ] ) ):
                if sortedListOfPoints[startingFork][i][1] == startingSequenceNumber:
                    originToAdd = sortedListOfPoints[startingFork][i]
                    sortedListOfPoints[forkNumber] = [originToAdd] + sortedListOfPoints[forkNumber]
                    break
    if time() - startSortTime > minimumTimeToOutput:
        print "Rearranged list in " + str( codeStuff.TimeOutput( startSortTime, time() ) )
    return sortedListOfPoints
    

def helpme():
    print "FUNCTIONS:"
    print
    print "getDirectionList( numDimensions )"
    print indent + " - Return list of coordinates that can be added/subtracted."
    print indent + " - Example:"
    print indent + indent + "   getDirectionList( 2 )"
    print indent + " - Output: "
    print indent + indent + "   [ [1,0],[-1,0],[0,1],[0,-1] ]"
    print
    print "timeOutput( startTime, endTime, decimals=2 )"
    print indent + " - Format time as a string."
    print indent + " - Example:"
    print indent + indent + "   timeOutput( startTime, time() )"
    print indent + " - Output: "
    print indent + indent + "   27.35 seconds"
    print
    print "infostore"
    print indent + " - Store values in the scene."
    print indent + " - Use infoStore.help() to view info."
    print
    print "shaders"
    print indent + " - Create smooth transitions of colour as shaders."
    print indent + " - Use shaders.help() to view info."
    print
    print "nameLoop( number ).getNextPrefix()"
    print indent + " - Used for multiple generations, will output a letter corresponding to the matching number."
    print
    print "cleanOldGenerations()"
    print indent + " - Will clean the stored values if the matching groups no longer exist."
    print
    print "drawCurves( letter )"
    print indent + " - Draw points in 3D as curves."
    print indent + " - The letter relates to what is assigned to the group."
    print
    print "sortByFork( listOfPoints, listOfStartingForks )"
    print indent + " - Return dictionary with fork numbers as the key."
    print indent + " - Starting forks are reqired to figure where the forks began."
    print
    print "simpleNameSpace( key = value, key2 = value2 )"
    print indent + " - Return dictionary with fork numbers as the key."
    print indent + " - Starting forks are reqired to figure where the forks began."
    
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################


#Get all directions the points can move in
possibleDirections = codeStuff.GetDirectionList( numDimensions )

#Setup variables
originPoint = []
for i in range( numDimensions ):
    originPoint.append( 0 )
originPoint = tuple( originPoint )
listOfStartingForks = {} #Where each fork originates for connecting purposes
listOfStartingForks[0] = -1
listOfPoints = {}
listOfPoints[originPoint] = [0,0,1]
'''listOfPoints[coordinates] = [fork, sequence number, percentDecrease]'''


#Store generation information
print "Storing generation information..."
if type( codeStuff.InfoStore( "numGenerations" ).read() ) != int:
    numGenerations = 0
else:
    numGenerations = codeStuff.InfoStore( "numGenerations" ).read() + 1
codeStuff.InfoStore( "numGenerations" ).set( numGenerations )
startStoreTime = time()
allGenerations = codeStuff.InfoStore( "allGenerations" ).read()
allGenerations.append( codeStuff.NameLoop( numGenerations ).getNextPrefix() )
codeStuff.InfoStore( "allGenerations" ).set( allGenerations )
if time() - startStoreTime > minimumTimeToOutput:
    print "Stored in " + str( codeStuff.TimeOutput( startStoreTime, time() ) )
#Create Group
originalSelection = py.ls( selection = True )
currentGroup = py.group( n = codeStuff.NameLoop( numGenerations ).getNextPrefix() + 'GenGroup', empty = True )
py.select( deselect = True )
#Generate Points
highestSequence = 0
totalPoints = 0
startTime = time()
nextTime = startTime + timeIncrement
print "Generating points..."
'''
listOfPoints (output)
startingLocation
forkLength
forkAmount
reduceRootAmount
maxAttemptsAtNewDirection
numDimensions
possibleDirections
reduceInSize
scaleAmount
sizeReduceAmount
locationPrecision
nearestNeighbourSearch
highestSequence (output)
currentFork

'''
for currentFork in range( 1, forkAmount+1 ):
    numberOfFails = 0
    #Pick random value from dictionary and use as starting point, start at origin for number of dimension points
    if currentFork < numDimensions:
        startingLocation = originPoint
    else:
        startingLocation = rd.choice( listOfPoints.keys() )
    
    startingFork = listOfPoints[startingLocation][0]
    startingSequence = listOfPoints[startingLocation][1]
    listOfStartingForks[currentFork] = startingFork
    #Start to build the individual fork
    for individualPoint in range( 1, forkLength+1 ):
        pointInSequence = individualPoint - numberOfFails
        #Try a certain amount of times if a fail
        for tries in range( 1, maxAttemptsAtNewDirection+1 ):
            newDirection = rd.randint( 1, numDimensions*2 )
            possibleNewDirection = possibleDirections[newDirection-1]
            #Figure how close point is to complete generation
            percentDecrease = 1 - (startingSequence+pointInSequence) / float( forkLength*forkAmount ) ** reduceRootAmount
            if percentDecrease > 1:
                percentDecrease = 1
            elif percentDecrease < 0:
                percentDecrease = 0
            #Make points get closer together
            if reduceInSize == True:
                sizeReduceAmount = percentDecrease
            else:
                sizeReduceAmount = 1
            #Add value to starting location
            possibleNewLocation = []
            for dimension in range( numDimensions ):
                possibleNewLocation.append( round( startingLocation[dimension] + scaleAmount * possibleNewDirection[dimension] * sizeReduceAmount, locationPrecision) )
            possibleNewLocation = tuple( possibleNewLocation )
            
            
            #Check if it already exists
            alreadyExists = False
            if nearestNeighbourSearch == True:
                for coordinates in listOfPoints:
                    #Use biggest bounding box
                    if listOfPoints[coordinates][2] > sizeReduceAmount:
                        rangeToCheck = pow( scaleAmount*cubeScale*listOfPoints[coordinates][2], 2 )
                    else:
                        rangeToCheck = pow( scaleAmount*cubeScale*percentDecrease, 2 )
                    nearestNeighbourSquared = rangeToCheck + 1
                    #Calculate distance to the point
                    distanceToPoint = 0
                    for i in range( numDimensions ):
                        distanceToPoint += pow( coordinates[i]-possibleNewLocation[i], 2 )
                    #Find if it is too close
                    if distanceToPoint < rangeToCheck:
                        alreadyExists = True
                        break
                
            if possibleNewLocation not in listOfPoints and alreadyExists == False:
                sequenceNumber = startingSequence+pointInSequence
                #Find highest number
                if sequenceNumber > highestSequence:
                    highestSequence = sequenceNumber
                listOfPoints[ possibleNewLocation ] = [currentFork, sequenceNumber, percentDecrease]
                startingLocation = possibleNewLocation
                totalPoints += 1
                #Output how far into generation it is
                if totalPoints % iterationsPoints == 0:
                    if time() > nextTime:
                        nextTime = time() + timeIncrement
                        #percentage = overall completion in forks + fork completion divided by total forks
                        percentageOverall = ( currentFork-1.0 )/forkAmount
                        percentageCurrentFork = individualPoint/float( forkLength*forkAmount )
                        percentage = percentageOverall + percentageCurrentFork
                        print indent + str( totalPoints ) + " points generated (" + str( round( percentage * 100, 2 ) ) + "%)"
                break
            #Count fails to stop incrementing sequence number
            if tries == maxAttemptsAtNewDirection:
                numberOfFails += 1

print objectsPerSecond( startTime, "points", totalPoints )               

startStoreTime = time()
print "Storing point information..."
codeStuff.UpdateViewport()

codeStuff.InfoStore( "PointList", currentGroup ).set( listOfPoints )
codeStuff.InfoStore( "StartingForks", currentGroup  ).set( listOfStartingForks )
py.addAttr( currentGroup, longName = "HighestSequence" )
py.addAttr( currentGroup, longName = "ReduceSize" )
py.setAttr( currentGroup + ".HighestSequence", highestSequence )
py.setAttr( currentGroup + ".ReduceSize", reduceInSize )

if time() - startStoreTime > minimumTimeToOutput:
    print "Stored in " + str( codeStuff.TimeOutput( startStoreTime, time() ) )


letter = codeStuff.InfoStore( "allGenerations" ).read()[-1]
sortedListOfPoints = sortByFork( codeStuff.InfoStore( "PointList", letter.lower() + "GenGroup" ).read(), codeStuff.InfoStore( "StartingForks", letter.lower() + "GenGroup" ).read() )

#Draw curves
if plotCurves == True:
    #Draw curve using latest generation
    drawCurves( letter )
    
#Draw cubes
if plotCubes == True:
    #Draw curve using latest generation
    drawCubes( letter )

#Remove any deleted groups from store
cleanOldGenerations()



#Build shaders
if drawShaders == True:
    startShaderTime = time()
    nextTime = startShaderTime + timeIncrement / 2
    print "Creating shaders..."
    codeStuff.UpdateViewport()
    shaderInfo = codeStuff.Shaders.create( ['magenta','yellow','green'], 10)
    #shaderInfo = codeStuff.Shaders.create( ['yellow','red','white','green','magenta','yellow','green'], 20)
    validColours = shaderInfo[0]
    validColours.reverse()
    numberOfShaders = shaderInfo[1]
    nameOfShaders = shaderInfo[2]
    print "Building list of cubes in scene..."
    codeStuff.UpdateViewport()
    try:
        cubeList = codeStuff.InfoStore( "CubeList", letter.lower() + "Cubes" ).read()
    except:
        cubeList = []
    #Check cubes exist first
    existingCubes = []
    if len( cubeList ) > 0:
        for i in range( len( cubeList ) ):
            try:
                existingCubes.append( str( py.ls( cubeList[i] )[0] ) )
            except:
                pass
    #If there are none
    maxCubes = float( len( existingCubes ) )
    if int( maxCubes ) == 0:
        print "No cubes found"
    else:
        print "Assigning colours to cubes..."  
    
    for i in range( int( maxCubes ) ): 
        #Setup shader details
        cubeName = existingCubes[i]
        colourValue = py.getAttr( cubeName + ".ColourValue" )
        shaderNumber = int( round( ( numberOfShaders-1 ) * colourValue, 0 ) )
        shaderName = nameOfShaders + str( shaderNumber )
        shaderSelect = shaderName
        cubeSelect = "|" + letter.lower() + "GenGroup" + "|" + letter.lower() + "Cubes" + "|" + cubeName + "|" + cubeName + "Shape.instObjGroups[0]"
        #Assign shader
        py.defaultNavigation( source = shaderSelect, destination = cubeSelect, connectToExisting = True )
        #Output progress
        if i % iterationsColour == 0:
            if time() > nextTime:
                nextTime = time() + timeIncrement
                percentage = i / maxCubes
                print indent + str( i ) + " cubes coloured (" + str( round( 100*percentage, 2 ) ) + "%)"
                codeStuff.UpdateViewport()
    
'''
validate( self, shaderColours, shaderAmount, isPerShader = True )
return shadercolours, shaderamount, shadername

py.defaultNavigation( source = shaderSelect, destination = cubeSelect, connectToExisting = True )
'''


py.select( originalSelection )
print "Done"
print
print "Overall time taken: " + str( codeStuff.TimeOutput( startTime, time() ) )
