try:
    import sha
    def generateUniqueID(data):
        return sha.new(data).hexdigest()
except ImportError:
    def generateUniqueID(data):
        generateUniqueID.sequence += 1
        return generateUniqueID.sequence
    generateUniqueID.sequence = 0

def getFilesize(file):
    file.seek(0, 2)
    size = file.tell()
    file.seek(0, 0)
    return size

