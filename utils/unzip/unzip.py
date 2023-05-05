import zipfile
import os
import sys
import shutil

def extractFile(directory, filename):
    srcPath = os.path.join(directory, filename)
    newDirName = filename.rsplit('.', 1)[0]
    newTargetPath = os.path.join(directory, newDirName)
    if os.path.exists(newTargetPath):
        print("同名文件或文件夹 [%s] 已经存在" % newDirName)
        return False
    os.mkdir(newTargetPath)
    extractFileOrder = []
    with zipfile.ZipFile(srcPath, 'r') as zf:
        try:
            for zipInfo in zf.infolist():
                try:
                    right_fn = zipInfo.filename.encode('cp437').decode('utf-8')
                except:
                    right_fn = zipInfo.filename.encode('cp437').decode('gbk')
                #print(right_fn)
                extractFileOrder.append(right_fn)
                if right_fn.find('._') == 0 or right_fn.find('__MACOSX') == 0:
                    extractFileOrder[-1] = extractFileOrder[-1] + ' *** ignored *** '
                    continue

                if zipInfo.is_dir():
                    os.mkdir(os.path.join(newTargetPath, right_fn))
                else:
                    with open(os.path.join(newTargetPath, right_fn), 'wb') as outputFile:
                        with zf.open(zipInfo.filename, 'r') as originFile:
                            shutil.copyfileobj(originFile, outputFile)

                #extractPath = Path(f.extract(fn, newTargetPath))
                #extractPath.rename(os.path.join(newTargetPath, fn.encode('cp437').decode('gbk')))
            #os.unlink(srcPath)
        except Exception as e:
            print('Part of extract file order:\n %s' % ('\n'.join(extractFileOrder)))
            print("解压文件 [%s] 失败: %s" % (filename, str(e)))
            return False
    #fileOpLogger.info('Extract file order:\n %s' % ('\n'.join(extractFileOrder)))
    return True


if __name__ == '__main__':
    selfDir = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) == 2:
        filenames = [sys.argv[1]]
    else:
        filenames = list(filter(lambda x: x.rsplit('.', 1)[-1].lower() == 'zip', os.listdir(selfDir)))
    for filename in filenames:
        extractFile(selfDir, filename)