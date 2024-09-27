import argparse
import conf.strings as text

def menu():
  parser = argparse.ArgumentParser(description="This code is used for the automatic generation of a 3D draft of an orthotic insole.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("-i", metavar="input", help="input directory", default="input")
  parser.add_argument("-o", metavar="output", help="output directory", default="output")
  parser.add_argument("-l", help="language selection", choices=['en','es'], default="en")
  args = parser.parse_args()
  return vars(args)

if __name__ == '__main__':
  print("This is a helper module for the insole-3Designer app.")