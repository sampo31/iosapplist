import sys

import cli.__main__

def main(argv=sys.argv):
 return cli.__main__.main(argv)

if __name__ == "__main__":
 try:
  sys.exit(main(sys.argv))
 except KeyboardInterrupt:
  pass
