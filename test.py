List = ["neet","code","love","you"]
s = ",".join(f"{len(s)}#{s}" for s in List)
print(s)

res, i = [],0

while i < len(s):
    j = i
    while str[j] != "#":
        j += 1
        length = int(s[i:j])
        res.append(s[j+1:j+1+length])
    print(res)
