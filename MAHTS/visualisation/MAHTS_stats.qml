<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.4.5-Madeira" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="1" minScale="1e+8" simplifyDrawingHints="0" simplifyMaxScale="1" readOnly="0" maxScale="10000" simplifyLocal="1" labelsEnabled="1" simplifyAlgorithm="0" simplifyDrawingTol="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 graduatedMethod="GraduatedColor" attr="if(  (&quot;sig_time&quot; &lt;=0.05), rate_time, NULL)" enableorderby="1" symbollevels="0" type="graduatedSymbol" forceraster="0">
    <ranges>
      <range label=" -20.00 - -2.50 " lower="-20.000000000000000" render="true" symbol="0" upper="-2.500000000000000"/>
      <range label=" -2.50 - -1.00 " lower="-2.500000000000000" render="true" symbol="1" upper="-1.000000000000000"/>
      <range label=" -1.00 - -0.60 " lower="-1.000000000000000" render="true" symbol="2" upper="-0.600000000000000"/>
      <range label=" -0.60 - -0.30 " lower="-0.600000000000000" render="true" symbol="3" upper="-0.300000000000000"/>
      <range label=" -0.30 - -0.10 " lower="-0.300000000000000" render="true" symbol="4" upper="-0.100000000000000"/>
      <range label=" -0.10 - 0.00 " lower="-0.100000000000000" render="true" symbol="5" upper="0.000000000000000"/>
      <range label=" 0.00 - 0.10 " lower="0.000000000000000" render="true" symbol="6" upper="0.100000000000000"/>
      <range label=" 0.10 - 0.30 " lower="0.100000000000000" render="true" symbol="7" upper="0.300000000000000"/>
      <range label=" 0.30 - 0.60 " lower="0.300000000000000" render="true" symbol="8" upper="0.600000000000000"/>
      <range label=" 0.60 - 1.00 " lower="0.600000000000000" render="true" symbol="9" upper="1.000000000000000"/>
      <range label=" 1.00 - 2.50 " lower="1.000000000000000" render="true" symbol="10" upper="2.500000000000000"/>
      <range label=" 2.50 - 20.00 " lower="2.500000000000000" render="true" symbol="11" upper="20.000000000000000"/>
    </ranges>
    <symbols>
      <symbol force_rhr="0" name="0" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="202,0,32,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="3.5"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="1" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="218,60,67,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="3"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="10" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="56,144,193,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="3"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="11" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="5,113,176,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="3.5"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="2" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="233,120,103,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2.5"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="3" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="245,173,141,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="4" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="246,203,183,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="1.5"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="5" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="247,232,226,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="1"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="6" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="229,238,243,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="1"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="7" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="192,220,234,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="1.5"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="8" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="155,202,225,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" name="9" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="107,174,210,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,0"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2.5"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <source-symbol>
      <symbol force_rhr="0" name="0" alpha="1" clip_to_extent="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="255,158,23,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,88"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </source-symbol>
    <colorramp name="[source]" type="gradient">
      <prop k="color1" v="202,0,32,255"/>
      <prop k="color2" v="5,113,176,255"/>
      <prop k="discrete" v="0"/>
      <prop k="rampType" v="gradient"/>
      <prop k="stops" v="0.25;244,165,130,255:0.5;247,247,247,255:0.75;146,197,222,255"/>
    </colorramp>
    <mode name="equal"/>
    <symmetricMode enabled="false" symmetryPoint="0" astride="false"/>
    <rotation/>
    <sizescale/>
    <labelformat decimalplaces="2" format=" %1 - %2 " trimtrailingzeroes="false"/>
    <orderby>
      <orderByClause nullsFirst="0" asc="1"> abs("rate_time" )</orderByClause>
    </orderby>
  </renderer-v2>
  <labeling type="simple">
    <settings>
      <text-style fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontWeight="50" multilineHeight="2" fontLetterSpacing="0" textColor="255,255,255,255" fieldName="concat(format_number( rate_time, 1), ' m') " fontFamily="Sans Serif" useSubstitutions="0" fontWordSpacing="0" fontSizeUnit="Point" namedStyle="Normal" fontStrikeout="0" fontSize="7" fontItalic="0" blendMode="0" isExpression="1" previewBkgrdColor="#ffffff" fontCapitals="0" textOpacity="1" fontUnderline="0">
        <text-buffer bufferNoFill="1" bufferSize="0.7778" bufferOpacity="0.5" bufferColor="0,0,0,255" bufferJoinStyle="128" bufferDraw="1" bufferSizeUnits="MM" bufferBlendMode="0" bufferSizeMapUnitScale="3x:0,0,0,0,0,0"/>
        <background shapeOpacity="1" shapeBlendMode="0" shapeRadiiUnit="MM" shapeRadiiX="5" shapeBorderWidthUnit="MM" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeY="5" shapeRadiiY="5" shapeSizeUnit="MM" shapeOffsetX="0" shapeOffsetUnit="MM" shapeDraw="0" shapeSizeX="5" shapeBorderWidth="0" shapeJoinStyle="64" shapeSVGFile="" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeType="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeBorderColor="128,128,128,0" shapeSizeType="0" shapeFillColor="255,255,255,0" shapeRotationType="0" shapeRotation="0" shapeOffsetY="0"/>
        <shadow shadowOffsetAngle="135" shadowScale="100" shadowRadius="1.5" shadowColor="255,255,255,255" shadowDraw="1" shadowUnder="0" shadowBlendMode="8" shadowOffsetGlobal="1" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusUnit="MM" shadowOffsetUnit="MM" shadowRadiusAlphaOnly="0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOpacity="1" shadowOffsetDist="1"/>
        <substitutions/>
      </text-style>
      <text-format wrapChar="" useMaxLineLengthForAutoWrap="1" autoWrapLength="0" multilineAlign="3" reverseDirectionSymbol="0" placeDirectionSymbol="0" formatNumbers="0" plussign="0" leftDirectionSymbol="&lt;" addDirectionSymbol="0" rightDirectionSymbol=">" decimals="3"/>
      <placement yOffset="0" offsetUnits="MM" priority="1" placement="1" centroidInside="0" centroidWhole="0" preserveRotation="1" xOffset="-5" maxCurvedCharAngleOut="-25" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" fitInPolygonOnly="0" quadOffset="3" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" repeatDistance="0" repeatDistanceUnits="MM" dist="0" distUnits="MM" placementFlags="10" maxCurvedCharAngleIn="25" rotationAngle="0" offsetType="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" distMapUnitScale="3x:0,0,0,0,0,0"/>
      <rendering fontMinPixelSize="3" obstacleFactor="1" zIndex="0" scaleVisibility="1" scaleMax="1000000" upsidedownLabels="0" drawLabels="1" mergeLines="0" minFeatureSize="0" fontMaxPixelSize="10000" fontLimitPixelSize="0" obstacle="1" scaleMin="0" displayAll="0" labelPerPart="0" obstacleType="0" maxNumLabels="20" limitNumLabels="0"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" name="name" type="QString"/>
          <Option name="properties"/>
          <Option value="collection" name="type" type="QString"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory minScaleDenominator="10000" scaleBasedVisibility="0" enabled="0" labelPlacementMethod="XHeight" diagramOrientation="Up" sizeScale="3x:0,0,0,0,0,0" barWidth="5" height="15" penWidth="0" penAlpha="255" rotationOffset="270" sizeType="MM" lineSizeScale="3x:0,0,0,0,0,0" penColor="#000000" scaleDependency="Area" backgroundAlpha="255" backgroundColor="#ffffff" opacity="1" width="15" minimumSize="0" lineSizeType="MM" maxScaleDenominator="1e+8">
      <fontProperties description="Sans Serif,9,-1,5,50,0,0,0,0,0" style=""/>
      <attribute field="" label="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings priority="0" showAll="1" placement="0" zIndex="0" linePlacementFlags="18" obstacle="0" dist="0">
    <properties>
      <Option type="Map">
        <Option value="" name="name" type="QString"/>
        <Option name="properties"/>
        <Option value="collection" name="type" type="QString"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="rate_time">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="rate_SOI">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="rate_IOD">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="rate_SAM">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="rate_IPO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="rate_PDO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="rate_tide">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="sig_time">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="sig_SOI">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="sig_IOD">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="sig_SAM">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="sig_IPO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="sig_PDO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="sig_tide">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="outl_time">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="outl_SOI">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="outl_IOD">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="outl_SAM">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="outl_IPO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="outl_PDO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="outl_tide">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1988">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1989">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1990">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1991">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1992">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1993">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1994">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1995">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1996">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1997">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1998">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="1999">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2000">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2001">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2002">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2003">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2004">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2005">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2006">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2007">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2008">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2009">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2010">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2011">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2012">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2013">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2014">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2015">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2016">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2017">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="2018">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="rate_time" name="" index="0"/>
    <alias field="rate_SOI" name="" index="1"/>
    <alias field="rate_IOD" name="" index="2"/>
    <alias field="rate_SAM" name="" index="3"/>
    <alias field="rate_IPO" name="" index="4"/>
    <alias field="rate_PDO" name="" index="5"/>
    <alias field="rate_tide" name="" index="6"/>
    <alias field="sig_time" name="" index="7"/>
    <alias field="sig_SOI" name="" index="8"/>
    <alias field="sig_IOD" name="" index="9"/>
    <alias field="sig_SAM" name="" index="10"/>
    <alias field="sig_IPO" name="" index="11"/>
    <alias field="sig_PDO" name="" index="12"/>
    <alias field="sig_tide" name="" index="13"/>
    <alias field="outl_time" name="" index="14"/>
    <alias field="outl_SOI" name="" index="15"/>
    <alias field="outl_IOD" name="" index="16"/>
    <alias field="outl_SAM" name="" index="17"/>
    <alias field="outl_IPO" name="" index="18"/>
    <alias field="outl_PDO" name="" index="19"/>
    <alias field="outl_tide" name="" index="20"/>
    <alias field="1988" name="" index="21"/>
    <alias field="1989" name="" index="22"/>
    <alias field="1990" name="" index="23"/>
    <alias field="1991" name="" index="24"/>
    <alias field="1992" name="" index="25"/>
    <alias field="1993" name="" index="26"/>
    <alias field="1994" name="" index="27"/>
    <alias field="1995" name="" index="28"/>
    <alias field="1996" name="" index="29"/>
    <alias field="1997" name="" index="30"/>
    <alias field="1998" name="" index="31"/>
    <alias field="1999" name="" index="32"/>
    <alias field="2000" name="" index="33"/>
    <alias field="2001" name="" index="34"/>
    <alias field="2002" name="" index="35"/>
    <alias field="2003" name="" index="36"/>
    <alias field="2004" name="" index="37"/>
    <alias field="2005" name="" index="38"/>
    <alias field="2006" name="" index="39"/>
    <alias field="2007" name="" index="40"/>
    <alias field="2008" name="" index="41"/>
    <alias field="2009" name="" index="42"/>
    <alias field="2010" name="" index="43"/>
    <alias field="2011" name="" index="44"/>
    <alias field="2012" name="" index="45"/>
    <alias field="2013" name="" index="46"/>
    <alias field="2014" name="" index="47"/>
    <alias field="2015" name="" index="48"/>
    <alias field="2016" name="" index="49"/>
    <alias field="2017" name="" index="50"/>
    <alias field="2018" name="" index="51"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" field="rate_time" applyOnUpdate="0"/>
    <default expression="" field="rate_SOI" applyOnUpdate="0"/>
    <default expression="" field="rate_IOD" applyOnUpdate="0"/>
    <default expression="" field="rate_SAM" applyOnUpdate="0"/>
    <default expression="" field="rate_IPO" applyOnUpdate="0"/>
    <default expression="" field="rate_PDO" applyOnUpdate="0"/>
    <default expression="" field="rate_tide" applyOnUpdate="0"/>
    <default expression="" field="sig_time" applyOnUpdate="0"/>
    <default expression="" field="sig_SOI" applyOnUpdate="0"/>
    <default expression="" field="sig_IOD" applyOnUpdate="0"/>
    <default expression="" field="sig_SAM" applyOnUpdate="0"/>
    <default expression="" field="sig_IPO" applyOnUpdate="0"/>
    <default expression="" field="sig_PDO" applyOnUpdate="0"/>
    <default expression="" field="sig_tide" applyOnUpdate="0"/>
    <default expression="" field="outl_time" applyOnUpdate="0"/>
    <default expression="" field="outl_SOI" applyOnUpdate="0"/>
    <default expression="" field="outl_IOD" applyOnUpdate="0"/>
    <default expression="" field="outl_SAM" applyOnUpdate="0"/>
    <default expression="" field="outl_IPO" applyOnUpdate="0"/>
    <default expression="" field="outl_PDO" applyOnUpdate="0"/>
    <default expression="" field="outl_tide" applyOnUpdate="0"/>
    <default expression="" field="1988" applyOnUpdate="0"/>
    <default expression="" field="1989" applyOnUpdate="0"/>
    <default expression="" field="1990" applyOnUpdate="0"/>
    <default expression="" field="1991" applyOnUpdate="0"/>
    <default expression="" field="1992" applyOnUpdate="0"/>
    <default expression="" field="1993" applyOnUpdate="0"/>
    <default expression="" field="1994" applyOnUpdate="0"/>
    <default expression="" field="1995" applyOnUpdate="0"/>
    <default expression="" field="1996" applyOnUpdate="0"/>
    <default expression="" field="1997" applyOnUpdate="0"/>
    <default expression="" field="1998" applyOnUpdate="0"/>
    <default expression="" field="1999" applyOnUpdate="0"/>
    <default expression="" field="2000" applyOnUpdate="0"/>
    <default expression="" field="2001" applyOnUpdate="0"/>
    <default expression="" field="2002" applyOnUpdate="0"/>
    <default expression="" field="2003" applyOnUpdate="0"/>
    <default expression="" field="2004" applyOnUpdate="0"/>
    <default expression="" field="2005" applyOnUpdate="0"/>
    <default expression="" field="2006" applyOnUpdate="0"/>
    <default expression="" field="2007" applyOnUpdate="0"/>
    <default expression="" field="2008" applyOnUpdate="0"/>
    <default expression="" field="2009" applyOnUpdate="0"/>
    <default expression="" field="2010" applyOnUpdate="0"/>
    <default expression="" field="2011" applyOnUpdate="0"/>
    <default expression="" field="2012" applyOnUpdate="0"/>
    <default expression="" field="2013" applyOnUpdate="0"/>
    <default expression="" field="2014" applyOnUpdate="0"/>
    <default expression="" field="2015" applyOnUpdate="0"/>
    <default expression="" field="2016" applyOnUpdate="0"/>
    <default expression="" field="2017" applyOnUpdate="0"/>
    <default expression="" field="2018" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint field="rate_time" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="rate_SOI" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="rate_IOD" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="rate_SAM" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="rate_IPO" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="rate_PDO" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="rate_tide" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="sig_time" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="sig_SOI" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="sig_IOD" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="sig_SAM" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="sig_IPO" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="sig_PDO" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="sig_tide" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="outl_time" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="outl_SOI" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="outl_IOD" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="outl_SAM" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="outl_IPO" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="outl_PDO" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="outl_tide" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1988" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1989" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1990" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1991" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1992" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1993" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1994" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1995" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1996" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1997" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1998" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="1999" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2000" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2001" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2002" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2003" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2004" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2005" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2006" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2007" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2008" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2009" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2010" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2011" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2012" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2013" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2014" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2015" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2016" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2017" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="2018" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="rate_time" exp=""/>
    <constraint desc="" field="rate_SOI" exp=""/>
    <constraint desc="" field="rate_IOD" exp=""/>
    <constraint desc="" field="rate_SAM" exp=""/>
    <constraint desc="" field="rate_IPO" exp=""/>
    <constraint desc="" field="rate_PDO" exp=""/>
    <constraint desc="" field="rate_tide" exp=""/>
    <constraint desc="" field="sig_time" exp=""/>
    <constraint desc="" field="sig_SOI" exp=""/>
    <constraint desc="" field="sig_IOD" exp=""/>
    <constraint desc="" field="sig_SAM" exp=""/>
    <constraint desc="" field="sig_IPO" exp=""/>
    <constraint desc="" field="sig_PDO" exp=""/>
    <constraint desc="" field="sig_tide" exp=""/>
    <constraint desc="" field="outl_time" exp=""/>
    <constraint desc="" field="outl_SOI" exp=""/>
    <constraint desc="" field="outl_IOD" exp=""/>
    <constraint desc="" field="outl_SAM" exp=""/>
    <constraint desc="" field="outl_IPO" exp=""/>
    <constraint desc="" field="outl_PDO" exp=""/>
    <constraint desc="" field="outl_tide" exp=""/>
    <constraint desc="" field="1988" exp=""/>
    <constraint desc="" field="1989" exp=""/>
    <constraint desc="" field="1990" exp=""/>
    <constraint desc="" field="1991" exp=""/>
    <constraint desc="" field="1992" exp=""/>
    <constraint desc="" field="1993" exp=""/>
    <constraint desc="" field="1994" exp=""/>
    <constraint desc="" field="1995" exp=""/>
    <constraint desc="" field="1996" exp=""/>
    <constraint desc="" field="1997" exp=""/>
    <constraint desc="" field="1998" exp=""/>
    <constraint desc="" field="1999" exp=""/>
    <constraint desc="" field="2000" exp=""/>
    <constraint desc="" field="2001" exp=""/>
    <constraint desc="" field="2002" exp=""/>
    <constraint desc="" field="2003" exp=""/>
    <constraint desc="" field="2004" exp=""/>
    <constraint desc="" field="2005" exp=""/>
    <constraint desc="" field="2006" exp=""/>
    <constraint desc="" field="2007" exp=""/>
    <constraint desc="" field="2008" exp=""/>
    <constraint desc="" field="2009" exp=""/>
    <constraint desc="" field="2010" exp=""/>
    <constraint desc="" field="2011" exp=""/>
    <constraint desc="" field="2012" exp=""/>
    <constraint desc="" field="2013" exp=""/>
    <constraint desc="" field="2014" exp=""/>
    <constraint desc="" field="2015" exp=""/>
    <constraint desc="" field="2016" exp=""/>
    <constraint desc="" field="2017" exp=""/>
    <constraint desc="" field="2018" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="&quot;move_abs&quot;" sortOrder="1">
    <columns>
      <column hidden="1" type="actions" width="-1"/>
      <column name="1988" hidden="0" type="field" width="-1"/>
      <column name="1989" hidden="0" type="field" width="-1"/>
      <column name="1990" hidden="0" type="field" width="-1"/>
      <column name="1991" hidden="0" type="field" width="-1"/>
      <column name="1992" hidden="0" type="field" width="-1"/>
      <column name="1993" hidden="0" type="field" width="-1"/>
      <column name="1994" hidden="0" type="field" width="-1"/>
      <column name="1995" hidden="0" type="field" width="-1"/>
      <column name="1996" hidden="0" type="field" width="-1"/>
      <column name="1997" hidden="0" type="field" width="-1"/>
      <column name="1998" hidden="0" type="field" width="-1"/>
      <column name="1999" hidden="0" type="field" width="-1"/>
      <column name="2000" hidden="0" type="field" width="-1"/>
      <column name="2001" hidden="0" type="field" width="-1"/>
      <column name="2002" hidden="0" type="field" width="-1"/>
      <column name="2003" hidden="0" type="field" width="-1"/>
      <column name="2004" hidden="0" type="field" width="-1"/>
      <column name="2005" hidden="0" type="field" width="-1"/>
      <column name="2006" hidden="0" type="field" width="-1"/>
      <column name="2007" hidden="0" type="field" width="-1"/>
      <column name="2008" hidden="0" type="field" width="-1"/>
      <column name="2009" hidden="0" type="field" width="-1"/>
      <column name="2010" hidden="0" type="field" width="-1"/>
      <column name="2011" hidden="0" type="field" width="-1"/>
      <column name="2012" hidden="0" type="field" width="-1"/>
      <column name="2013" hidden="0" type="field" width="-1"/>
      <column name="2014" hidden="0" type="field" width="-1"/>
      <column name="2015" hidden="0" type="field" width="-1"/>
      <column name="2016" hidden="0" type="field" width="-1"/>
      <column name="2017" hidden="0" type="field" width="-1"/>
      <column name="rate_time" hidden="0" type="field" width="-1"/>
      <column name="sig_time" hidden="0" type="field" width="-1"/>
      <column name="outl_time" hidden="0" type="field" width="-1"/>
      <column name="rate_SOI" hidden="0" type="field" width="-1"/>
      <column name="sig_SOI" hidden="0" type="field" width="-1"/>
      <column name="outl_SOI" hidden="0" type="field" width="-1"/>
      <column name="rate_IOD" hidden="0" type="field" width="-1"/>
      <column name="rate_SAM" hidden="0" type="field" width="-1"/>
      <column name="rate_IPO" hidden="0" type="field" width="-1"/>
      <column name="rate_PDO" hidden="0" type="field" width="-1"/>
      <column name="sig_IOD" hidden="0" type="field" width="-1"/>
      <column name="sig_SAM" hidden="0" type="field" width="-1"/>
      <column name="sig_IPO" hidden="0" type="field" width="-1"/>
      <column name="sig_PDO" hidden="0" type="field" width="-1"/>
      <column name="outl_IOD" hidden="0" type="field" width="-1"/>
      <column name="outl_SAM" hidden="0" type="field" width="-1"/>
      <column name="outl_IPO" hidden="0" type="field" width="-1"/>
      <column name="outl_PDO" hidden="0" type="field" width="-1"/>
      <column name="2018" hidden="0" type="field" width="-1"/>
      <column name="rate_tide" hidden="0" type="field" width="-1"/>
      <column name="sig_tide" hidden="0" type="field" width="-1"/>
      <column name="outl_tide" hidden="0" type="field" width="-1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field editable="1" name="1987-01-01"/>
    <field editable="1" name="1988"/>
    <field editable="1" name="1988-01-01"/>
    <field editable="1" name="1989"/>
    <field editable="1" name="1989-01-01"/>
    <field editable="1" name="1990"/>
    <field editable="1" name="1990-01-01"/>
    <field editable="1" name="1991"/>
    <field editable="1" name="1991-01-01"/>
    <field editable="1" name="1992"/>
    <field editable="1" name="1992-01-01"/>
    <field editable="1" name="1993"/>
    <field editable="1" name="1993-01-01"/>
    <field editable="1" name="1994"/>
    <field editable="1" name="1994-01-01"/>
    <field editable="1" name="1995"/>
    <field editable="1" name="1995-01-01"/>
    <field editable="1" name="1996"/>
    <field editable="1" name="1996-01-01"/>
    <field editable="1" name="1997"/>
    <field editable="1" name="1997-01-01"/>
    <field editable="1" name="1998"/>
    <field editable="1" name="1998-01-01"/>
    <field editable="1" name="1999"/>
    <field editable="1" name="1999-01-01"/>
    <field editable="1" name="2000"/>
    <field editable="1" name="2000-01-01"/>
    <field editable="1" name="2001"/>
    <field editable="1" name="2001-01-01"/>
    <field editable="1" name="2002"/>
    <field editable="1" name="2002-01-01"/>
    <field editable="1" name="2003"/>
    <field editable="1" name="2003-01-01"/>
    <field editable="1" name="2004"/>
    <field editable="1" name="2004-01-01"/>
    <field editable="1" name="2005"/>
    <field editable="1" name="2005-01-01"/>
    <field editable="1" name="2006"/>
    <field editable="1" name="2006-01-01"/>
    <field editable="1" name="2007"/>
    <field editable="1" name="2007-01-01"/>
    <field editable="1" name="2008"/>
    <field editable="1" name="2008-01-01"/>
    <field editable="1" name="2009"/>
    <field editable="1" name="2009-01-01"/>
    <field editable="1" name="2010"/>
    <field editable="1" name="2010-01-01"/>
    <field editable="1" name="2011"/>
    <field editable="1" name="2011-01-01"/>
    <field editable="1" name="2012"/>
    <field editable="1" name="2012-01-01"/>
    <field editable="1" name="2013"/>
    <field editable="1" name="2013-01-01"/>
    <field editable="1" name="2014"/>
    <field editable="1" name="2014-01-01"/>
    <field editable="1" name="2015"/>
    <field editable="1" name="2015-01-01"/>
    <field editable="1" name="2016"/>
    <field editable="1" name="2016-01-01"/>
    <field editable="1" name="2017"/>
    <field editable="1" name="2017-01-01"/>
    <field editable="1" name="2018"/>
    <field editable="1" name="2018-01-01"/>
    <field editable="1" name="breakpoints"/>
    <field editable="1" name="eln_outl"/>
    <field editable="1" name="eln_rate"/>
    <field editable="1" name="eln_sig"/>
    <field editable="1" name="incpt_IOD"/>
    <field editable="1" name="incpt_IPO"/>
    <field editable="1" name="incpt_PDO"/>
    <field editable="1" name="incpt_SAM"/>
    <field editable="1" name="incpt_SOI"/>
    <field editable="1" name="incpt_tide"/>
    <field editable="1" name="incpt_time"/>
    <field editable="1" name="lan_outl"/>
    <field editable="1" name="lan_rate"/>
    <field editable="1" name="lan_sig"/>
    <field editable="1" name="mov_outl"/>
    <field editable="1" name="mov_rate"/>
    <field editable="1" name="mov_sig"/>
    <field editable="1" name="move_abs"/>
    <field editable="1" name="neg_outl"/>
    <field editable="1" name="neg_rate"/>
    <field editable="1" name="neg_sig"/>
    <field editable="1" name="orig_ogc_fid"/>
    <field editable="1" name="outl_IOD"/>
    <field editable="1" name="outl_IPO"/>
    <field editable="1" name="outl_PDO"/>
    <field editable="1" name="outl_SAM"/>
    <field editable="1" name="outl_SOI"/>
    <field editable="1" name="outl_tide"/>
    <field editable="1" name="outl_time"/>
    <field editable="1" name="pos_outl"/>
    <field editable="1" name="pos_rate"/>
    <field editable="1" name="pos_sig"/>
    <field editable="1" name="rate_IOD"/>
    <field editable="1" name="rate_IPO"/>
    <field editable="1" name="rate_PDO"/>
    <field editable="1" name="rate_SAM"/>
    <field editable="1" name="rate_SOI"/>
    <field editable="1" name="rate_tide"/>
    <field editable="1" name="rate_time"/>
    <field editable="1" name="sig_IOD"/>
    <field editable="1" name="sig_IPO"/>
    <field editable="1" name="sig_PDO"/>
    <field editable="1" name="sig_SAM"/>
    <field editable="1" name="sig_SOI"/>
    <field editable="1" name="sig_tide"/>
    <field editable="1" name="sig_time"/>
    <field editable="1" name="soi_outl"/>
    <field editable="1" name="soi_rate"/>
    <field editable="1" name="soi_sig"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="1987-01-01"/>
    <field labelOnTop="0" name="1988"/>
    <field labelOnTop="0" name="1988-01-01"/>
    <field labelOnTop="0" name="1989"/>
    <field labelOnTop="0" name="1989-01-01"/>
    <field labelOnTop="0" name="1990"/>
    <field labelOnTop="0" name="1990-01-01"/>
    <field labelOnTop="0" name="1991"/>
    <field labelOnTop="0" name="1991-01-01"/>
    <field labelOnTop="0" name="1992"/>
    <field labelOnTop="0" name="1992-01-01"/>
    <field labelOnTop="0" name="1993"/>
    <field labelOnTop="0" name="1993-01-01"/>
    <field labelOnTop="0" name="1994"/>
    <field labelOnTop="0" name="1994-01-01"/>
    <field labelOnTop="0" name="1995"/>
    <field labelOnTop="0" name="1995-01-01"/>
    <field labelOnTop="0" name="1996"/>
    <field labelOnTop="0" name="1996-01-01"/>
    <field labelOnTop="0" name="1997"/>
    <field labelOnTop="0" name="1997-01-01"/>
    <field labelOnTop="0" name="1998"/>
    <field labelOnTop="0" name="1998-01-01"/>
    <field labelOnTop="0" name="1999"/>
    <field labelOnTop="0" name="1999-01-01"/>
    <field labelOnTop="0" name="2000"/>
    <field labelOnTop="0" name="2000-01-01"/>
    <field labelOnTop="0" name="2001"/>
    <field labelOnTop="0" name="2001-01-01"/>
    <field labelOnTop="0" name="2002"/>
    <field labelOnTop="0" name="2002-01-01"/>
    <field labelOnTop="0" name="2003"/>
    <field labelOnTop="0" name="2003-01-01"/>
    <field labelOnTop="0" name="2004"/>
    <field labelOnTop="0" name="2004-01-01"/>
    <field labelOnTop="0" name="2005"/>
    <field labelOnTop="0" name="2005-01-01"/>
    <field labelOnTop="0" name="2006"/>
    <field labelOnTop="0" name="2006-01-01"/>
    <field labelOnTop="0" name="2007"/>
    <field labelOnTop="0" name="2007-01-01"/>
    <field labelOnTop="0" name="2008"/>
    <field labelOnTop="0" name="2008-01-01"/>
    <field labelOnTop="0" name="2009"/>
    <field labelOnTop="0" name="2009-01-01"/>
    <field labelOnTop="0" name="2010"/>
    <field labelOnTop="0" name="2010-01-01"/>
    <field labelOnTop="0" name="2011"/>
    <field labelOnTop="0" name="2011-01-01"/>
    <field labelOnTop="0" name="2012"/>
    <field labelOnTop="0" name="2012-01-01"/>
    <field labelOnTop="0" name="2013"/>
    <field labelOnTop="0" name="2013-01-01"/>
    <field labelOnTop="0" name="2014"/>
    <field labelOnTop="0" name="2014-01-01"/>
    <field labelOnTop="0" name="2015"/>
    <field labelOnTop="0" name="2015-01-01"/>
    <field labelOnTop="0" name="2016"/>
    <field labelOnTop="0" name="2016-01-01"/>
    <field labelOnTop="0" name="2017"/>
    <field labelOnTop="0" name="2017-01-01"/>
    <field labelOnTop="0" name="2018"/>
    <field labelOnTop="0" name="2018-01-01"/>
    <field labelOnTop="0" name="breakpoints"/>
    <field labelOnTop="0" name="eln_outl"/>
    <field labelOnTop="0" name="eln_rate"/>
    <field labelOnTop="0" name="eln_sig"/>
    <field labelOnTop="0" name="incpt_IOD"/>
    <field labelOnTop="0" name="incpt_IPO"/>
    <field labelOnTop="0" name="incpt_PDO"/>
    <field labelOnTop="0" name="incpt_SAM"/>
    <field labelOnTop="0" name="incpt_SOI"/>
    <field labelOnTop="0" name="incpt_tide"/>
    <field labelOnTop="0" name="incpt_time"/>
    <field labelOnTop="0" name="lan_outl"/>
    <field labelOnTop="0" name="lan_rate"/>
    <field labelOnTop="0" name="lan_sig"/>
    <field labelOnTop="0" name="mov_outl"/>
    <field labelOnTop="0" name="mov_rate"/>
    <field labelOnTop="0" name="mov_sig"/>
    <field labelOnTop="0" name="move_abs"/>
    <field labelOnTop="0" name="neg_outl"/>
    <field labelOnTop="0" name="neg_rate"/>
    <field labelOnTop="0" name="neg_sig"/>
    <field labelOnTop="0" name="orig_ogc_fid"/>
    <field labelOnTop="0" name="outl_IOD"/>
    <field labelOnTop="0" name="outl_IPO"/>
    <field labelOnTop="0" name="outl_PDO"/>
    <field labelOnTop="0" name="outl_SAM"/>
    <field labelOnTop="0" name="outl_SOI"/>
    <field labelOnTop="0" name="outl_tide"/>
    <field labelOnTop="0" name="outl_time"/>
    <field labelOnTop="0" name="pos_outl"/>
    <field labelOnTop="0" name="pos_rate"/>
    <field labelOnTop="0" name="pos_sig"/>
    <field labelOnTop="0" name="rate_IOD"/>
    <field labelOnTop="0" name="rate_IPO"/>
    <field labelOnTop="0" name="rate_PDO"/>
    <field labelOnTop="0" name="rate_SAM"/>
    <field labelOnTop="0" name="rate_SOI"/>
    <field labelOnTop="0" name="rate_tide"/>
    <field labelOnTop="0" name="rate_time"/>
    <field labelOnTop="0" name="sig_IOD"/>
    <field labelOnTop="0" name="sig_IPO"/>
    <field labelOnTop="0" name="sig_PDO"/>
    <field labelOnTop="0" name="sig_SAM"/>
    <field labelOnTop="0" name="sig_SOI"/>
    <field labelOnTop="0" name="sig_tide"/>
    <field labelOnTop="0" name="sig_time"/>
    <field labelOnTop="0" name="soi_outl"/>
    <field labelOnTop="0" name="soi_rate"/>
    <field labelOnTop="0" name="soi_sig"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>1987-01-01</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
