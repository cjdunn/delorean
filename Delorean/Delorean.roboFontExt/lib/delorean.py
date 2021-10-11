# !/usr/bin/env python

# Delorean: Interpolation Preview by CJ Dunn.
# Thanks to Frederik Berlaen and David Jonathan Ross.


import vanilla
from mojo.roboFont import CurrentFont, AllFonts, CurrentGlyph
from fontParts.world import RGlyph
from mojo.glyphPreview import GlyphPreview
from mojo.UI import SliderEditStepper
from mojo.subscriber import Subscriber, WindowController, registerCurrentGlyphSubscriber


class DeloreanController(Subscriber, WindowController):

    def build(self):
        self.value = .5
        self.font1 = self.font2 = None

        x = 10
        y = 10
        lineHeight = 23

        g = CurrentGlyph()
        if g is not None:
            ginit = g.name
        else:
            ginit = ""

        # use minSize to make window re-sizable
        self.w = vanilla.Window(
            (400, 400),
            'Delorean: Interpolation Preview',
            minSize=(200, 200)
        )
        # Dropdown menus
        w_width = self.w.getPosSize()[2]
        menu_width = w_width/2 - 15

        # It would be nice to make the dropdown respond to a width change,
        # of the window, but that is for next time.
        self.w.leftList = vanilla.PopUpButton(
            (x, y, menu_width, lineHeight), [],
            callback=self.fontChangedCallback)
        self.w.rightList = vanilla.PopUpButton(
            (-menu_width-x, y, menu_width, lineHeight), [],
            callback=self.fontChangedCallback)

        # Line Return
        y += lineHeight

        # vanilla.TextBox (not interactive field)
        self.w.gnameTextBox = vanilla.TextBox(
            (x, y, 200, lineHeight), 'Glyph name')
        self.w.valueTextBox = vanilla.TextBox(
            (x+105, y, 200, lineHeight), 'Interpolation %')

        # Line Return
        y += lineHeight

        # "Glyph name"
        self.w.gnameTextInput = vanilla.EditText(
            (x, y, 80, lineHeight), ginit,
            callback=self.setterButtonCallback)

        # "Percentage" Slider
        # Value
        self.w.valueTextInput = SliderEditStepper(
            (x+105, y, -10, 22),
            minValue=-200, maxValue=400, value=50, increment=10,
            callback=self.setterButtonCallback)

        y += lineHeight
        y += 15

        # -5 from bottom
        self.w.preview = GlyphPreview((0, y, -0, -5))

        # Report
        self.w.reportText = vanilla.TextBox(
            (x, -27, 400, lineHeight), '')

        # generate instance
        self.w.generate = vanilla.Button(
            (-35, -27, 27, lineHeight),
            "⬇", callback=self.generateCallback)

        self.populateDropdownMenus()

        self.w.box = vanilla.Box((0, (y-9), -0, -30))
        self.w.open()

    def fontChangedCallback(self, sender):
        if len(self.available_fonts) < 2:
            self.font1 = self.font2 = None
        else:
            self.font1 = self.available_fonts[self.w.leftList.get()]
            self.font2 = self.available_fonts[self.w.rightList.get()]

        self.setterButtonCallback()

    def setterButtonCallback(self, sender=None):
        self.value = float(self.w.valueTextInput.get()) / 100
        self.interpolateSetGlyph(self.w.gnameTextInput.get())

    def generateCallback(self, sender):
        gname = self.w.gnameTextInput.get()

        f = CurrentFont()

        pcnt = int((self.value)*100)
        instanceName = f'{gname}.{pcnt}'

        if gname in self.font1 and gname in self.font2:
            i = self.interpolate(gname)

            i.name = instanceName

            f.insertGlyph(i)

            print(f'\nGlyph "{instanceName}" added to CurrentFont()')

    def populateDropdownMenus(self):
        self.available_fonts = AllFonts()
        # Figuring out what to display in the dropdown list
        styleNames_set = False
        familyNames_set = False
        familyNames_differ = False

        if all([f.info.styleName for f in self.available_fonts]):
            styleNames_set = True
        if all([f.info.familyName for f in self.available_fonts]):
            familyNames_set = True
            if len(set([f.info.familyName for f in self.available_fonts])) > 1:
                familyNames_differ = True

        if styleNames_set:
            # If style names are all set and family name is all the same
            # (or not set), display only the style name.
            # If family names are different, display family name & style name.
            if familyNames_set:
                if familyNames_differ:
                    fontList = [f'{f.info.familyName} {f.info.styleName}' for f in self.available_fonts]
                else:
                    fontList = [f.info.styleName for f in self.available_fonts]
            else:
                fontList = [f.info.styleName for f in self.available_fonts]

        elif familyNames_set and familyNames_differ:
            # If for some reason only the family name is set, check if it is
            # different across UFOs. If it is, use it.
            fontList = [f.info.familyName for f in self.available_fonts]
        else:
            # Last resort (neither family nor style name are set), or the
            # family name is the same across UFOs (and no style name set):
            # Only display the font object as a string.
            fontList = [f'{f}' for f in self.available_fonts]

        self.w.leftList.setItems(fontList)
        self.w.rightList.setItems(fontList)

        self.w.leftList.set(0)
        self.w.rightList.set(1)

        self.fontChangedCallback(self.w.leftList)

    def fontDocumentDidOpenNew(self, info):
        self.populateDropdownMenus()

    def fontDocumentDidOpen(self, info):
        self.populateDropdownMenus()

    def fontDocumentDidClose(self, info):
        self.populateDropdownMenus()

    def roboFontDidSwitchCurrentGlyph(self, info):
        glyph = info["glyph"]
        if glyph is None:
            self.interpolateSetGlyph(None)
        else:
            self.interpolateSetGlyph(glyph.name)

    def currentGlyphDidChange(self, info):
        self.interpolateSetGlyph(info["glyph"].name)

    def interpolateSetGlyph(self, gname):
        if gname is None:
            self.w.gnameTextInput.set("")
            self.w.preview.setGlyph(None)
            return
        self.w.gnameTextInput.set(gname)

        self.updateReport(gname)
        i = self.interpolate(gname)
        if gname and self.font1 is not None:
            # scales upm to 1000
            upm = self.font1.info.unitsPerEm
            scale_factor = 1000/float(upm)
            offset = (self.font2[gname].width) / 2
            i.scaleBy((scale_factor, scale_factor), origin=(offset, 0))

        self.w.preview.setGlyph(i)

    def updateReport(self, gname):
        reportText = ''
        if self.font1 is None or self.font2 is None:
            reportText = "Open Some Fonts"
        elif not gname:
            reportText = "Select a glyph"
        elif gname in self.font1 and gname in self.font2:
            glyph1 = self.font1[gname]
            glyph2 = self.font2[gname]

            report = glyph1.isCompatible(glyph2)
            if not report[0]:
                # no good
                reportText = f"😡 *** /{gname} is not compatible for interpolation ***"
            else:
                # Status: good
                reportText = "😎"

        self.w.reportText.set(reportText)

    def interpolate(self, gname):
        if self.font1 is None or self.font2 is None:
            return None
        if not gname:
            return None

        if len(self.font1[gname].components) > 0 or len(self.font2[gname].components) > 0:
            srcGlyph1 = self.font1[gname]
            glyph1 = self.decomposeComponents(self.font1, srcGlyph1)

            srcGlyph2 = self.font2[gname]
            glyph2 = self.decomposeComponents(self.font2, srcGlyph2)

        else:
            glyph1 = self.font1[gname]
            glyph2 = self.font2[gname]

        dest = RGlyph()
        dest.interpolate(self.value, glyph1, glyph2)
        return dest

    def decomposeComponents(self, font, srcGlyph):
        from mojo.pens import DecomposePointPen
        dstGlyph = RGlyph()

        # copy the width of the source glyph to the destination glyph
        dstGlyph.width = srcGlyph.width

        # get a pen to draw into the destination glyph
        dstPen = dstGlyph.getPointPen()

        # create a decompose pen which writes its result into the destination pen
        decomposePen = DecomposePointPen(font, dstPen)

        # draw the source glyph into the decompose pen
        # which draws into the destination pen
        # which draws into the destination glyph
        srcGlyph.drawPoints(decomposePen)

        return dstGlyph


if __name__ == '__main__':
    registerCurrentGlyphSubscriber(DeloreanController)
