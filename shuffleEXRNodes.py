#first arg must be location of arg

nuke.menu('Nodes').addCommand('CustomScripts/Shuffle EXR Channels', shuffleChannelLayers)

plus = 'plus'
multiply = 'multiply'
over = 'over'

dif = ['dif', 'color']
light = ['spec', 'refl', 'refx', 'light', 'refraction', 'refract']
shadow = ['gi', 'shadow', 'occlusion', 'fresnel']

passDict = {'dif' : dif, 'light' : light, 'shadow' : shadow}


def uniqueChannelLayerList(nodeToProcess):
    rawChannelList = nodeToProcess.channels()
    channelLayerList = []
    for channel in rawChannelList:
        channelLayer = channel.split('.')
        channelLayerList.append(channelLayer[0])
    return list(set(channelLayerList))

# getting the selection and filtering to a list of read nodes

def shuffleChannelLayers():
    selectedNodes = nuke.selectedNodes()
    for readNode in selectedNodes:
        #test if it's a read node
        if readNode.Class() == 'Read':
            #grabs our list of channel layers from the unique channel layer list function
            uniqueChannelLayers = sortChannelList(uniqueChannelLayerList(readNode))
			
			layerTypeCounter = 0 
            for layerType in uniqueChannelLayers:
				if layerTypeCounter == 0:
					mode = 'over'
				elif layerTypeCounter == 1:
					mode = 'plus'
				elif layerTypeCounter == 2:
					mode = 'multiply'
				elif layerTypeCounter == 3:
					mode = 'over'
				
				for channelLayer in layerType:
					print 'layerTypeCounter = ', layerTypeCounter, 'channelLayer = ', channelLayer
					#create a shuffle node for channelLayer
					shuffleNode = nuke.nodes.Shuffle(name = 'Shuffle_' + channelLayer, postage_stamp = True)
					#set the channel
					shuffleNode.knob('in').setValue(channelLayer)
					# set first input to the read node
					shuffleNode.setInput(0, readNode)
					#create a variable that creates a curvetool, that will connect to shuffleNode and perform autocrop
					curveNode = nuke.nodes.CurveTool(name = 'AutoCrop_' + channelLayer, 
																		inputs = [shuffleNode],
																		operation = 'Auto Crop')
					
					nuke.execute(curveNode, readNode.knob('first').value(), readNode.knob('last').value())
					cropNode = nuke.nodes.Crop(name = 'Crop_' + channelLayer, inputs = [curveNode])
					cropNode.knob('box').copyAnimations(curveNode.knob('autocropdata').animations())
					
					
					#give unique name to first finished shuffled channel
					if layerType.index(channelLayer) == 0 and layerTypeCounter == 0:
						global firstNode
						firstNode = cropNode
					
					elif layerType.index(channelLayer) == 0 and layerTypeCounter == 1:
						createMergeNode(cropNode, firstNode, mode, channelLayer)
					#create first merge node with B input connected to current node, and A into the first node
					elif layerType.index(channelLayer) >= 1 and layerTypeCounter > 0:
						createMergeNode(cropNode, mergeNode, mode, channelLayer)
					
					elif layerType.index(channelLayer) >= 0 and layerTypeCounter > 1:
						createMergeNode(cropNode, mergeNode, mode, channelLayer)
					
					#elif layerType.index(channelLayer) >= 0 and layerTypeCounter > 0:
					#	createMergeNode(cropNode, firstNode, mode, channelLayer)
					#create subsequent merge nodes with B input to previous merge, A to current node
					
				layerTypeCounter += 1
							
								
            
def sortChannelList(listUser):
	### The list template will be based on renderer. In the final script, this will more likely be a separate dictionary
	### for each renderer, separating passes into diffusion, specular, and shadow passes -> so we can make sure they merge in the proper modes
	### 
	listDifTemp = ['diffuse']
	listLightTemp = ['spec', 'refl']
	listShadowTemp = ['shadow', 'ambient_occlusion']
	
	listDif = []
	listLight = []
	listShadow = []
	
	
	print "listUser: ", listUser
	for userChan in listUser:
		for channelName in listDifTemp:
			buf = "Searching for %s in %s\n" % (channelName, userChan)
			print buf
			if channelName in userChan.lower():
				listDif.append(userChan)
				matchLocation = listUser.index(userChan)
				print "popping", matchLocation
				listUser.pop(listUser.index(userChan))
				#adds 'null' to index we just popped, to maintain position index position in loop
				listUser.insert(matchLocation, 'null')
				print listUser
				
			
		
		for channelName in listLightTemp:
			buf = "Searching for %s in %s\n" % (channelName, userChan)
			print buf
			if channelName in userChan.lower():
				listLight.append(userChan)
				matchLocation = listUser.index(userChan)
				print "popping", matchLocation
				listUser.pop(listUser.index(userChan))
				listUser.insert(matchLocation, 'null')
				print listUser
				
		for channelName in listShadowTemp:
			buf = "Searching for %s in %s\n" % (channelName, userChan)
			print buf
			if channelName in userChan.lower():
				listShadow.append(userChan)
				matchLocation = listUser.index(userChan)
				print "popping", matchLocation
				listUser.pop(listUser.index(userChan))
				listUser.insert(matchLocation, 'null')
				print listUser
		
		
	#eliminates duplicates left over in listUser		
	listExtra = list(set(listUser))
	print 'listExtra: ', listExtra
	#eliminates 'null' from final listUser
	listExtra.pop(listExtra.index('null'))
	
	listFinal = [listDif, listLight, listShadow, listExtra]
	print listFinal
	return listFinal

#Creates a dot and mergenode based on the two inputs and the mode. 	
def createMergeNode(input1, input2, mode, channelLayer):
	global mergeNode
	print mode + 'ing %s to %s\n' % (input1.knob('name').value(), input2.knob('name').value())
	dot = nuke.nodes.Dot(inputs = [input1])
	dot.setXYpos(input1.xpos() + input1.screenWidth()/2, input2.ypos() + 100)
	newMergeNode = nuke.nodes.Merge(name = 'Merge_' + channelLayer, operation = mode)
	newMergeNode.setInput(0, input2)
	newMergeNode.setInput(1, dot)
	newMergeNode.setXYpos(input2.xpos(), dot.ypos())
	mergeNode = newMergeNode
	return
	
	
shuffleChannelLayers()

