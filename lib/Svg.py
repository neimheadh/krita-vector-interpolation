import re
import xml.etree.ElementTree as ET

# Attribute namespace
class Attribute:
    """
    ---------------------------------------------
    |               Attributes                  |
    ---------------------------------------------
    """
    # Path "d" attribute command 
    class Command:
        """ 
        Path d attribute command 

        Attributes
        ----------
        operation : str
            Command operation
        values: int[]
            List of command values

        Methods
        -------
        clone() : Command
            Clone command
        """

        def __init__(self, s = None):
            """
            Parameters
            ----------
            s: unqique d attribute command string
            """
            self.operation = None
            self.values = []

            if s:
                self.operation = re.search(r'[M|L|H|V|C|S|Q|T|A|Z]', s)[0]
                values = re.findall(r'[0-9\.-]+', s)
                
                self.values = []
                for v in values:
                    self.values.append(float(v))

        def toString(self):
            s = self.operation

            for v in self.values:
                s +=  ' ' + str(v)

            return s

    # "transform" attribute
    class Transform:
        """ 
        Transform attributes
        """
        def __init__(self, s = None):
            """
            Paremeters
            ==========
            s : string
               Transform attribute value
            """
            self.operation = None
            self.values = []

            if s:
                m = re.search(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\(?([^\)]*)\)?', s)
                self.operation = m[1]
                if m[2]:
                    for v in re.findall(r'[0-9\.-]+', m[2]):
                        self.values.append(float(v))
        
        def clone(self):
            """Clone transform operation"""
            new = self.__class__(self.operation)
            new.values = []
            
            for v in self.values:
                new.values.append(v)

            return new
        
        def interpolated(self, transform, p):
            """
            Get interpolated transform

            Parameters
            =========
            transform : Transform
                Interpolation final transform
            p: float
                Interpolation factor
            """
            # Handle different operation
            t1 = self
            t2 = transform

            if t1.operation == 'translate' and t2.operation == 'matrix':
                t1 = self.translateToMatrix(t1)
            elif t1.operation == 'matrix' and t2.operation == 'translate':
                t2 = self.translateToMatrix(t2)
            if t1.operation != t2.operation:
                raise RuntimeError('Cannot interpolate a different transform operation')

            # Load transform values
            values = []
            for i, v1 in enumerate(t1.values):
                try:
                    v2 = t2.values[i]
                except IndexError:
                    v2 = 0.0

                values.append([v1, v2])
            
            # Load second transform values if this transform has more
            if len(transform.values) > len(values):
                l = len(values)
                for i in range(len(transform.values) - l):
                    values.append([0.0, transform.values[i + l]])
            
            intp = t1.clone()
            intp.values = []
            for v in values:
                intp.values.append((v[1] - v[0]) * p + v[0])

            return intp

        def toString(self):
            """ Transform string """
            s = self.operation + '('
            for i in range(len(self.values)):
                s += ', ' if i else ''
                s += str(self.values[i])
            s += ')'

            return s
        
        def translateToMatrix(self, trans):
            """
            Transform a translate transform into a matrix transform

            Parameters
            ----------
            trans: Transform
              Translate operation
            """
            if trans.operation == 'translate':
                matrix = self.__class__()
                matrix.operation = 'matrix'
                matrix.values = [1, 0, 0, 1]
                matrix.values.append(trans.values[0] if len(trans.values) > 0 else 0)
                matrix.values.append(trans.values[1] if len(trans.values) > 1 else 0)

                return matrix

            return trans

# Node namespace
class Node:
    """
    -----------------------------------------------
    |                 Nodes                       |
    -----------------------------------------------
    """

    # Node main class
    class Node:
        """
        SVG node main class.

        Attributes
        ----------
        el: ET.Element
            DOM element.
        transform: Attribute.Transform[]
            List of transormations
        
        Methods
        -------
        clone(): Node
            Clone node.
        canInterpolate(node: Node): bool
            Inheritable. Check if the interation is compatible with the given node.
        toString(): str
            Transform into string.
        """

        def __init__(self, s):
            """
            Parameters
            ----------
            s : string|ET.Element
                Node xml representation or element
            """
            self.el = s if type(s) == ET.Element else ET.fromstring(s)

            self.transform = []
            if self.el.attrib.get('transform'):
                m = re.findall(r"([a-zA-Z][a-zA-Z0-9_]*\([^\)]*\))", self.el.attrib['transform'])
                for t in m:
                    self.transform.append(Attribute.Transform(t))

        def interpolated(self, node, p):
            """
            Return a node interpolation between current and a given
            node.

            Create a node with its transformations interpolated

            Parameters
            ----------
            node : Node
                Interpolation limit
            p : float
                Interpolation multiplier
            """

            if len(self.transform) > 1 or len(node.transform) > 1:
                raise RuntimeError('Interpolation can only manage a maximum of one transform')

            # Copy current node
            new = self.clone()

            # Get transforms. Handle case one of node has no transform and the other does
            transforms = []
            if len(self.transform) == len(node.transform):
                transforms += self.transform
                transforms += node.transform
            else:
                if len(self.transform) < len(node.transform):
                    transforms.append(node.transform[0].clone())
                    transforms.append(node.transform[0])
                    for i, _ in enumerate(transforms[0].values):
                        transforms[0].values[i] = 0.0
                if len(node.transform) < len(self.transform):
                    transforms.append(self.transform[0])
                    transforms.append(self.transform[0].clone())
                    for i, _ in enumerate(transforms[1].values):
                        transforms[1].values[i] = 0.0
            # Change transforms to interpolated
            if len(transforms):
                new.transform = [transforms[0].interpolated(transforms[1], p)]

            return new

        def canInterpolate(self, node):
            """ 
            Check if the node can interpolate the given node.

            Parameters
            ----------
            node : Node
                Compared node.
            """
            return type(node) == self.__class__

        def clone(self):
            """ Clone node """
            new = self.__class__(ET.tostring(self.el))
            return new
        
        def interpolate(self, node, steps):
            """
            Return list of interpolation between current node and given node

            Parameters
            -----------
            node: Node
                Interpreation limit node
            steps: int
                Number of interpretations between current node and given node
            """

            intl = []

            if not self.canInterpolate(node):
                raise RuntimeError('Node not compatible with node for interpolation')
            
            for i in range(steps):
                p = (i+1) / (steps + 1)
                intl.append(self.interpolated(node, p))
            
            return intl

        def stringAttributes(self):
            """Get list of overrided attributes by toString()"""
            
            # Attributes replacing self.el attributes
            attr = {'id': None}

            if len(self.transform):
                # Build transformation attribute to override el trans attribute
                trans = ''
                for t in self.transform:
                    trans += ';' + t.toString() if trans else t.toString()
                attr['transform'] = trans
            
            return attr

        def toString(self, xmlns = {}, addXmlns = False):
            """ 
            String conversion
        
            Parameters
            ----------
            self : object
                Converted node
            xmlns : object
                Url -> node SVG xmlns object
            addXmlns : bool
                Add xmlns into root node
            """
            # Initialize string
            s = f'<{self.el.tag}'

            if addXmlns:
                for url in xmlns:
                    s += f' xmlns{':' + xmlns[url] if xmlns[url] else ''}="{url}"'

            # Load attributes
            stringAttributes = self.stringAttributes()
            attrib = {}
            for a in self.el.attrib:
                # We first load ET.Element attributes
                attrib[a] = self.el.attrib[a]
            for a in stringAttributes:
                # Then override managed attributes
                attrib[a] = stringAttributes[a]
            for a in attrib:
                s += f' {a}="{attrib[a]}"' if attrib[a] != None else ''

            s += ' />'
            # Replace namespace link by namepace names
            for url in xmlns:
                s = s.replace('{' + url + '}', f'{xmlns[url]}:' if xmlns[url] else '')
            
            return s
    
    # <path> node
    class Path(Node):
        """
        SVG node <path>

        Attributes
        ----------
        commands: Path.Command[]
            List of path commands
        
        Methods
        -------
        clone(): Path
            Clone path.
        parseValues()
            Parse values.
        """

        def __init__(self, s):
            """
            Parameters
            ----------
            s : string|ET.Element
                Node xml representation or element
            """
            super().__init__(s)

            # Parse values
            d = self.el.attrib['d'] if self.el.attrib.get('d') else ''
            commands = re.findall(r"[M|L|H|V|C|S|Q|T|A|Z][0-9-\.\s]*", d)
            self.commands = []
            for command in commands:
                self.commands.append(Attribute.Command(command))

        def canInterpolate(self, node):
            """ 
            Check if the node can interpolate the given node.

            Parameters
            ----------
            node : Node
                Compared node.
            """
            if not super().canInterpolate(node):
                return False
            
            l = len(self.commands)
            if l != len(node.commands):
                return False

            for i in range(l):
                c1 = self.commands[i]
                c2 = node.commands[i]

                if c1.operation != c2.operation:
                    return False

            return True
        
        def interpolate(self, node, steps):
            '''
            Return list of interpolation between current node a1nd given node

            Parameters
            -----------
            node: Node
                Interpreation limit node
            steps: int
                Number of interpretations between current node and given node
            '''
            intr = super().interpolate(node, steps)

            for i, path in enumerate(intr):
                path = intr[i]
                p = (i + 1) / (steps + 1)
                
                for c, command in enumerate(path.commands):
                    values = command.values

                    command.values = []
                    for v, v1 in enumerate(values):
                        v2 = node.commands[c].values[v]
                        command.values.append((v2 - v1) * p + v1)


            return intr

        
        def stringAttributes(self): 
            """Get list of overrided attributes by toString()"""
            attr = super().stringAttributes()
            attr['d'] = ''

            for command in self.commands:
                attr['d'] += command.toString()

            return attr


# Svg file
class Svg:
    """
    SVG file

    Properties
    ----------
    children : Node[]
        SVG children nodes
    el : ET.Element
        DOM Element
    """


    def __init__(self, s = None):
        """
        Parameters
        ----------
        s : string
          svg string representation
        """
        self.children = []
        self.el = ET.Element('svg')

        if s :
            # Load xmlns
            self.xmlns = re.findall(r'\sxmlns:?([^=]*)="([^"]+)"', s)
            
            for x in self.xmlns:
                ET.register_namespace(x[0], x[1])
        
            # Parse xml
            self.el = ET.fromstring(s)

            # Search in children list ignoring namespaves
            for child in self.el:
                if re.search(r'{?[^}]*}?path', child.tag):
                    self.children.append(Node.Path(child))
                else:
                    self.children.append(Node.Node(child))
    
    def clone(self):
        """ Clone svg object """
        new = self.__class__()
        new.xmlns = self.xmlns
        new.el = ET.Element(self.el.tag)
        new.el.attrib = self.el.attrib

        return new
    
    def getXmlns(self):
        """ Return xmlns list object """
        xmlns = {}
        for x in self.xmlns:
            xmlns[x[1]] = x[0]
        return xmlns
    
    def interpolate(self, node1, node2, steps, new = True):
        """
        Generate nodes interpolation, into current Svg object
        or into a new one.

        Parameters
        ----------
        node1 : int|string|Node.Node
            First node position in children, or id, or object
        node2 : int|string|Node.Node
            Second node position in children, or id, or object
        steps: int
            Number of interpolations
        new: bool
            If False, generate interpolations in current object
        """

        # Get destination Svg
        if not new:
            svg = self
        else:
            # Same Svg but without children
            svg = self.clone()

        # Get nodes objects
        if type(node1) == int:
            node1 = self.children[node1]
        if type(node2) == int:
            node2 = self.children[node2]
        
        if type(node1) == str:
            for node in self.children:
                if node.el.attrib.get('id') == node1:
                    node1 = node
                    break

        if type(node2) == str:
            for node in self.children:
                if node.el.attrib.get('id') == node2:
                    node2 = node
                    break

        # Interpolate & add interpolated nodes
        try:
            intp = node1.interpolate(node2, steps)
        except RuntimeError:
            raise RuntimeError(
                'Nodes are not compatible for interpolation' + "\n\n" +
                'node 1 : ' + node1.toString() + "\n"
                'node 2 : ' + node2.toString()
            )
        
        for node in intp:
            svg.children.append(node)

        return svg

    def toString(self):
        """ String conversion """
        s = '<svg'

        # Load xmlns
        xmlns = self.getXmlns()
        for url in xmlns:
            ns = xmlns[url]
            s += f' xmlns{':' if ns else ''}{ns}="{url}"'

        # Load attributes
        for a  in self.el.attrib:
            s += f' {a}="{self.el.attrib[a]}"'
        
        # Load children
        if len(self.children):
            s += '>'
            for child in self.children:
                s += f"\n\t{child.toString(xmlns)}"
            s += "\n</svg>"
        else:
            s += ' />'

        # Replace namespace link by namepace names
        for url in xmlns:
            s = s.replace(f'{{url}}', f'{xmlns[url]}:' if xmlns[url] else '')
        
        return s