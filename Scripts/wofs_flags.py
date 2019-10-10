### WOFLs are stored as bit flags, when viewing these it's sometimes hard to know which bits are set.
## Run with:  python wofs_flags.py

flags = {1: "No data", 2: "Non contiguous", 4: "Sea", 8: "Terrain or low solar angle",
 16: "High slope", 32: "Cloud shadow", 64: "Cloud", 128: "Water"}



if __name__=='__main__':

  wofl_value = int(input("Enter your wofs bit value to find out which flags are set: "))

  print(f"\nWOfS flags set to get WOFL value of {wofl_value}:")
  for v in sorted(flags.keys(), reverse=True):
    if wofl_value >= v:
      print(f" - {flags[v]}")
      wofl_value -= v