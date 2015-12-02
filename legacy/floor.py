
class Floor:

    def make(self, o, wall):
        """
        Make a floor for a single wall part
        """
        o = wall.getCornerEmpty(o)
        left = o["l"]
        closed = wall.isClosed()
        origin = o if closed else wall.getStart(left)
        
        empties = []
        o = origin
        while True:
            empties.append(o)
            o = wall.getNext(o)
            if o == origin or not o:
                break
        self.makeFromEmpties(empties)