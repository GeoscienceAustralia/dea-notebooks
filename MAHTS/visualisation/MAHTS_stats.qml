<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis labelsEnabled="1" simplifyDrawingHints="0" version="3.4.5-Madeira" minScale="1e+8" simplifyDrawingTol="1" simplifyLocal="1" maxScale="10000" readOnly="0" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="1" simplifyMaxScale="1" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="graduatedSymbol" enableorderby="1" graduatedMethod="GraduatedColor" symbollevels="0" forceraster="0" attr="if(  (&quot;sig_time&quot; &lt;=0.05), rate_time, NULL)">
    <ranges>
      <range upper="-2.500000000000000" label=" -20.00 - -2.50 " render="true" symbol="0" lower="-20.000000000000000"/>
      <range upper="-1.000000000000000" label=" -2.50 - -1.00 " render="true" symbol="1" lower="-2.500000000000000"/>
      <range upper="-0.600000000000000" label=" -1.00 - -0.60 " render="true" symbol="2" lower="-1.000000000000000"/>
      <range upper="-0.300000000000000" label=" -0.60 - -0.30 " render="true" symbol="3" lower="-0.600000000000000"/>
      <range upper="-0.100000000000000" label=" -0.30 - -0.10 " render="true" symbol="4" lower="-0.300000000000000"/>
      <range upper="0.000000000000000" label=" -0.10 - 0.00 " render="true" symbol="5" lower="-0.100000000000000"/>
      <range upper="0.100000000000000" label=" 0.00 - 0.10 " render="true" symbol="6" lower="0.000000000000000"/>
      <range upper="0.300000000000000" label=" 0.10 - 0.30 " render="true" symbol="7" lower="0.100000000000000"/>
      <range upper="0.600000000000000" label=" 0.30 - 0.60 " render="true" symbol="8" lower="0.300000000000000"/>
      <range upper="1.000000000000000" label=" 0.60 - 1.00 " render="true" symbol="9" lower="0.600000000000000"/>
      <range upper="2.500000000000000" label=" 1.00 - 2.50 " render="true" symbol="10" lower="1.000000000000000"/>
      <range upper="20.000000000000000" label=" 2.50 - 20.00 " render="true" symbol="11" lower="2.500000000000000"/>
    </ranges>
    <symbols>
      <symbol name="0" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="1" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="10" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="11" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="2" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="3" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="4" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="5" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="6" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="7" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="8" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="9" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <source-symbol>
      <symbol name="0" clip_to_extent="1" force_rhr="0" type="marker" alpha="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
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
    <symmetricMode astride="false" enabled="false" symmetryPoint="0"/>
    <rotation/>
    <sizescale/>
    <labelformat format=" %1 - %2 " decimalplaces="2" trimtrailingzeroes="false"/>
    <orderby>
      <orderByClause nullsFirst="0" asc="1"> abs("rate_time" )</orderByClause>
    </orderby>
  </renderer-v2>
  <labeling type="simple">
    <settings>
      <text-style textColor="255,255,255,255" isExpression="1" fieldName="concat(format_number( rate_time, 1), ' m') " namedStyle="Normal" fontSize="7" textOpacity="1" fontWordSpacing="0" useSubstitutions="0" fontLetterSpacing="0" fontFamily="Sans Serif" blendMode="0" multilineHeight="2" fontSizeUnit="Point" fontCapitals="0" fontStrikeout="0" fontItalic="0" fontWeight="50" fontUnderline="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" previewBkgrdColor="#ffffff">
        <text-buffer bufferNoFill="1" bufferJoinStyle="128" bufferOpacity="1" bufferSize="0" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferDraw="0" bufferBlendMode="0" bufferColor="255,255,255,255" bufferSizeUnits="MM"/>
        <background shapeFillColor="255,255,255,0" shapeRadiiUnit="MM" shapeBorderWidthUnit="MM" shapeType="0" shapeRotationType="0" shapeSizeX="5" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetUnit="MM" shapeSizeType="0" shapeDraw="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeBlendMode="0" shapeOffsetX="0" shapeOffsetY="0" shapeBorderWidth="0" shapeBorderColor="128,128,128,0" shapeRotation="0" shapeSVGFile="" shapeRadiiX="5" shapeSizeUnit="MM" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeJoinStyle="64" shapeRadiiY="5" shapeOpacity="1" shapeSizeY="5" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0"/>
        <shadow shadowDraw="1" shadowScale="100" shadowUnder="0" shadowRadiusAlphaOnly="0" shadowColor="255,255,255,255" shadowOffsetUnit="MM" shadowRadius="1.5" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOpacity="1" shadowOffsetDist="1" shadowRadiusUnit="MM" shadowOffsetAngle="135" shadowOffsetGlobal="1" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowBlendMode="8"/>
        <substitutions/>
      </text-style>
      <text-format formatNumbers="0" placeDirectionSymbol="0" autoWrapLength="0" multilineAlign="3" addDirectionSymbol="0" plussign="0" rightDirectionSymbol=">" wrapChar="" leftDirectionSymbol="&lt;" decimals="3" useMaxLineLengthForAutoWrap="1" reverseDirectionSymbol="0"/>
      <placement fitInPolygonOnly="0" maxCurvedCharAngleOut="-25" xOffset="-5" dist="0" offsetUnits="MM" maxCurvedCharAngleIn="25" rotationAngle="0" preserveRotation="1" quadOffset="3" repeatDistanceUnits="MM" priority="1" repeatDistance="0" offsetType="0" placementFlags="10" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" centroidWhole="0" placement="1" centroidInside="0" distMapUnitScale="3x:0,0,0,0,0,0" distUnits="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" yOffset="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0"/>
      <rendering limitNumLabels="0" scaleVisibility="0" fontMaxPixelSize="10000" maxNumLabels="20" fontLimitPixelSize="0" upsidedownLabels="0" displayAll="0" labelPerPart="0" obstacleType="0" zIndex="0" scaleMax="0" mergeLines="0" obstacleFactor="1" scaleMin="0" fontMinPixelSize="3" minFeatureSize="0" obstacle="1" drawLabels="1"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" type="QString" value=""/>
          <Option name="properties"/>
          <Option name="type" type="QString" value="collection"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>
  <customproperties>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory labelPlacementMethod="XHeight" lineSizeType="MM" scaleBasedVisibility="0" rotationOffset="270" enabled="0" lineSizeScale="3x:0,0,0,0,0,0" diagramOrientation="Up" penAlpha="255" minScaleDenominator="15000" scaleDependency="Area" penColor="#000000" height="15" width="15" maxScaleDenominator="1e+8" barWidth="5" sizeScale="3x:0,0,0,0,0,0" minimumSize="0" penWidth="0" opacity="1" backgroundAlpha="255" sizeType="MM" backgroundColor="#ffffff">
      <fontProperties style="" description="Sans Serif,9,-1,5,50,0,0,0,0,0"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings dist="0" showAll="1" zIndex="0" obstacle="0" placement="0" linePlacementFlags="18" priority="0">
    <properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties"/>
        <Option name="type" type="QString" value="collection"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
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
    <alias name="" index="0" field="rate_time"/>
    <alias name="" index="1" field="rate_SOI"/>
    <alias name="" index="2" field="rate_IOD"/>
    <alias name="" index="3" field="rate_SAM"/>
    <alias name="" index="4" field="rate_IPO"/>
    <alias name="" index="5" field="rate_PDO"/>
    <alias name="" index="6" field="rate_tide"/>
    <alias name="" index="7" field="sig_time"/>
    <alias name="" index="8" field="sig_SOI"/>
    <alias name="" index="9" field="sig_IOD"/>
    <alias name="" index="10" field="sig_SAM"/>
    <alias name="" index="11" field="sig_IPO"/>
    <alias name="" index="12" field="sig_PDO"/>
    <alias name="" index="13" field="sig_tide"/>
    <alias name="" index="14" field="outl_time"/>
    <alias name="" index="15" field="outl_SOI"/>
    <alias name="" index="16" field="outl_IOD"/>
    <alias name="" index="17" field="outl_SAM"/>
    <alias name="" index="18" field="outl_IPO"/>
    <alias name="" index="19" field="outl_PDO"/>
    <alias name="" index="20" field="outl_tide"/>
    <alias name="" index="21" field="1988"/>
    <alias name="" index="22" field="1989"/>
    <alias name="" index="23" field="1990"/>
    <alias name="" index="24" field="1991"/>
    <alias name="" index="25" field="1992"/>
    <alias name="" index="26" field="1993"/>
    <alias name="" index="27" field="1994"/>
    <alias name="" index="28" field="1995"/>
    <alias name="" index="29" field="1996"/>
    <alias name="" index="30" field="1997"/>
    <alias name="" index="31" field="1998"/>
    <alias name="" index="32" field="1999"/>
    <alias name="" index="33" field="2000"/>
    <alias name="" index="34" field="2001"/>
    <alias name="" index="35" field="2002"/>
    <alias name="" index="36" field="2003"/>
    <alias name="" index="37" field="2004"/>
    <alias name="" index="38" field="2005"/>
    <alias name="" index="39" field="2006"/>
    <alias name="" index="40" field="2007"/>
    <alias name="" index="41" field="2008"/>
    <alias name="" index="42" field="2009"/>
    <alias name="" index="43" field="2010"/>
    <alias name="" index="44" field="2011"/>
    <alias name="" index="45" field="2012"/>
    <alias name="" index="46" field="2013"/>
    <alias name="" index="47" field="2014"/>
    <alias name="" index="48" field="2015"/>
    <alias name="" index="49" field="2016"/>
    <alias name="" index="50" field="2017"/>
    <alias name="" index="51" field="2018"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" field="rate_time" expression=""/>
    <default applyOnUpdate="0" field="rate_SOI" expression=""/>
    <default applyOnUpdate="0" field="rate_IOD" expression=""/>
    <default applyOnUpdate="0" field="rate_SAM" expression=""/>
    <default applyOnUpdate="0" field="rate_IPO" expression=""/>
    <default applyOnUpdate="0" field="rate_PDO" expression=""/>
    <default applyOnUpdate="0" field="rate_tide" expression=""/>
    <default applyOnUpdate="0" field="sig_time" expression=""/>
    <default applyOnUpdate="0" field="sig_SOI" expression=""/>
    <default applyOnUpdate="0" field="sig_IOD" expression=""/>
    <default applyOnUpdate="0" field="sig_SAM" expression=""/>
    <default applyOnUpdate="0" field="sig_IPO" expression=""/>
    <default applyOnUpdate="0" field="sig_PDO" expression=""/>
    <default applyOnUpdate="0" field="sig_tide" expression=""/>
    <default applyOnUpdate="0" field="outl_time" expression=""/>
    <default applyOnUpdate="0" field="outl_SOI" expression=""/>
    <default applyOnUpdate="0" field="outl_IOD" expression=""/>
    <default applyOnUpdate="0" field="outl_SAM" expression=""/>
    <default applyOnUpdate="0" field="outl_IPO" expression=""/>
    <default applyOnUpdate="0" field="outl_PDO" expression=""/>
    <default applyOnUpdate="0" field="outl_tide" expression=""/>
    <default applyOnUpdate="0" field="1988" expression=""/>
    <default applyOnUpdate="0" field="1989" expression=""/>
    <default applyOnUpdate="0" field="1990" expression=""/>
    <default applyOnUpdate="0" field="1991" expression=""/>
    <default applyOnUpdate="0" field="1992" expression=""/>
    <default applyOnUpdate="0" field="1993" expression=""/>
    <default applyOnUpdate="0" field="1994" expression=""/>
    <default applyOnUpdate="0" field="1995" expression=""/>
    <default applyOnUpdate="0" field="1996" expression=""/>
    <default applyOnUpdate="0" field="1997" expression=""/>
    <default applyOnUpdate="0" field="1998" expression=""/>
    <default applyOnUpdate="0" field="1999" expression=""/>
    <default applyOnUpdate="0" field="2000" expression=""/>
    <default applyOnUpdate="0" field="2001" expression=""/>
    <default applyOnUpdate="0" field="2002" expression=""/>
    <default applyOnUpdate="0" field="2003" expression=""/>
    <default applyOnUpdate="0" field="2004" expression=""/>
    <default applyOnUpdate="0" field="2005" expression=""/>
    <default applyOnUpdate="0" field="2006" expression=""/>
    <default applyOnUpdate="0" field="2007" expression=""/>
    <default applyOnUpdate="0" field="2008" expression=""/>
    <default applyOnUpdate="0" field="2009" expression=""/>
    <default applyOnUpdate="0" field="2010" expression=""/>
    <default applyOnUpdate="0" field="2011" expression=""/>
    <default applyOnUpdate="0" field="2012" expression=""/>
    <default applyOnUpdate="0" field="2013" expression=""/>
    <default applyOnUpdate="0" field="2014" expression=""/>
    <default applyOnUpdate="0" field="2015" expression=""/>
    <default applyOnUpdate="0" field="2016" expression=""/>
    <default applyOnUpdate="0" field="2017" expression=""/>
    <default applyOnUpdate="0" field="2018" expression=""/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="rate_time"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="rate_SOI"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="rate_IOD"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="rate_SAM"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="rate_IPO"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="rate_PDO"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="rate_tide"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="sig_time"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="sig_SOI"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="sig_IOD"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="sig_SAM"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="sig_IPO"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="sig_PDO"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="sig_tide"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="outl_time"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="outl_SOI"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="outl_IOD"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="outl_SAM"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="outl_IPO"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="outl_PDO"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="outl_tide"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1988"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1989"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1990"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1991"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1992"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1993"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1994"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1995"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1996"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1997"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1998"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="1999"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2000"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2001"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2002"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2003"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2004"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2005"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2006"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2007"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2008"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2009"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2010"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2011"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2012"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2013"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2014"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2015"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2016"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2017"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="2018"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" field="rate_time" desc=""/>
    <constraint exp="" field="rate_SOI" desc=""/>
    <constraint exp="" field="rate_IOD" desc=""/>
    <constraint exp="" field="rate_SAM" desc=""/>
    <constraint exp="" field="rate_IPO" desc=""/>
    <constraint exp="" field="rate_PDO" desc=""/>
    <constraint exp="" field="rate_tide" desc=""/>
    <constraint exp="" field="sig_time" desc=""/>
    <constraint exp="" field="sig_SOI" desc=""/>
    <constraint exp="" field="sig_IOD" desc=""/>
    <constraint exp="" field="sig_SAM" desc=""/>
    <constraint exp="" field="sig_IPO" desc=""/>
    <constraint exp="" field="sig_PDO" desc=""/>
    <constraint exp="" field="sig_tide" desc=""/>
    <constraint exp="" field="outl_time" desc=""/>
    <constraint exp="" field="outl_SOI" desc=""/>
    <constraint exp="" field="outl_IOD" desc=""/>
    <constraint exp="" field="outl_SAM" desc=""/>
    <constraint exp="" field="outl_IPO" desc=""/>
    <constraint exp="" field="outl_PDO" desc=""/>
    <constraint exp="" field="outl_tide" desc=""/>
    <constraint exp="" field="1988" desc=""/>
    <constraint exp="" field="1989" desc=""/>
    <constraint exp="" field="1990" desc=""/>
    <constraint exp="" field="1991" desc=""/>
    <constraint exp="" field="1992" desc=""/>
    <constraint exp="" field="1993" desc=""/>
    <constraint exp="" field="1994" desc=""/>
    <constraint exp="" field="1995" desc=""/>
    <constraint exp="" field="1996" desc=""/>
    <constraint exp="" field="1997" desc=""/>
    <constraint exp="" field="1998" desc=""/>
    <constraint exp="" field="1999" desc=""/>
    <constraint exp="" field="2000" desc=""/>
    <constraint exp="" field="2001" desc=""/>
    <constraint exp="" field="2002" desc=""/>
    <constraint exp="" field="2003" desc=""/>
    <constraint exp="" field="2004" desc=""/>
    <constraint exp="" field="2005" desc=""/>
    <constraint exp="" field="2006" desc=""/>
    <constraint exp="" field="2007" desc=""/>
    <constraint exp="" field="2008" desc=""/>
    <constraint exp="" field="2009" desc=""/>
    <constraint exp="" field="2010" desc=""/>
    <constraint exp="" field="2011" desc=""/>
    <constraint exp="" field="2012" desc=""/>
    <constraint exp="" field="2013" desc=""/>
    <constraint exp="" field="2014" desc=""/>
    <constraint exp="" field="2015" desc=""/>
    <constraint exp="" field="2016" desc=""/>
    <constraint exp="" field="2017" desc=""/>
    <constraint exp="" field="2018" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortExpression="&quot;move_abs&quot;" actionWidgetStyle="dropDown" sortOrder="1">
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
    <field name="1987-01-01" editable="1"/>
    <field name="1988" editable="1"/>
    <field name="1988-01-01" editable="1"/>
    <field name="1989" editable="1"/>
    <field name="1989-01-01" editable="1"/>
    <field name="1990" editable="1"/>
    <field name="1990-01-01" editable="1"/>
    <field name="1991" editable="1"/>
    <field name="1991-01-01" editable="1"/>
    <field name="1992" editable="1"/>
    <field name="1992-01-01" editable="1"/>
    <field name="1993" editable="1"/>
    <field name="1993-01-01" editable="1"/>
    <field name="1994" editable="1"/>
    <field name="1994-01-01" editable="1"/>
    <field name="1995" editable="1"/>
    <field name="1995-01-01" editable="1"/>
    <field name="1996" editable="1"/>
    <field name="1996-01-01" editable="1"/>
    <field name="1997" editable="1"/>
    <field name="1997-01-01" editable="1"/>
    <field name="1998" editable="1"/>
    <field name="1998-01-01" editable="1"/>
    <field name="1999" editable="1"/>
    <field name="1999-01-01" editable="1"/>
    <field name="2000" editable="1"/>
    <field name="2000-01-01" editable="1"/>
    <field name="2001" editable="1"/>
    <field name="2001-01-01" editable="1"/>
    <field name="2002" editable="1"/>
    <field name="2002-01-01" editable="1"/>
    <field name="2003" editable="1"/>
    <field name="2003-01-01" editable="1"/>
    <field name="2004" editable="1"/>
    <field name="2004-01-01" editable="1"/>
    <field name="2005" editable="1"/>
    <field name="2005-01-01" editable="1"/>
    <field name="2006" editable="1"/>
    <field name="2006-01-01" editable="1"/>
    <field name="2007" editable="1"/>
    <field name="2007-01-01" editable="1"/>
    <field name="2008" editable="1"/>
    <field name="2008-01-01" editable="1"/>
    <field name="2009" editable="1"/>
    <field name="2009-01-01" editable="1"/>
    <field name="2010" editable="1"/>
    <field name="2010-01-01" editable="1"/>
    <field name="2011" editable="1"/>
    <field name="2011-01-01" editable="1"/>
    <field name="2012" editable="1"/>
    <field name="2012-01-01" editable="1"/>
    <field name="2013" editable="1"/>
    <field name="2013-01-01" editable="1"/>
    <field name="2014" editable="1"/>
    <field name="2014-01-01" editable="1"/>
    <field name="2015" editable="1"/>
    <field name="2015-01-01" editable="1"/>
    <field name="2016" editable="1"/>
    <field name="2016-01-01" editable="1"/>
    <field name="2017" editable="1"/>
    <field name="2017-01-01" editable="1"/>
    <field name="2018" editable="1"/>
    <field name="2018-01-01" editable="1"/>
    <field name="breakpoints" editable="1"/>
    <field name="eln_outl" editable="1"/>
    <field name="eln_rate" editable="1"/>
    <field name="eln_sig" editable="1"/>
    <field name="incpt_IOD" editable="1"/>
    <field name="incpt_IPO" editable="1"/>
    <field name="incpt_PDO" editable="1"/>
    <field name="incpt_SAM" editable="1"/>
    <field name="incpt_SOI" editable="1"/>
    <field name="incpt_tide" editable="1"/>
    <field name="incpt_time" editable="1"/>
    <field name="lan_outl" editable="1"/>
    <field name="lan_rate" editable="1"/>
    <field name="lan_sig" editable="1"/>
    <field name="mov_outl" editable="1"/>
    <field name="mov_rate" editable="1"/>
    <field name="mov_sig" editable="1"/>
    <field name="move_abs" editable="1"/>
    <field name="neg_outl" editable="1"/>
    <field name="neg_rate" editable="1"/>
    <field name="neg_sig" editable="1"/>
    <field name="orig_ogc_fid" editable="1"/>
    <field name="outl_IOD" editable="1"/>
    <field name="outl_IPO" editable="1"/>
    <field name="outl_PDO" editable="1"/>
    <field name="outl_SAM" editable="1"/>
    <field name="outl_SOI" editable="1"/>
    <field name="outl_tide" editable="1"/>
    <field name="outl_time" editable="1"/>
    <field name="pos_outl" editable="1"/>
    <field name="pos_rate" editable="1"/>
    <field name="pos_sig" editable="1"/>
    <field name="rate_IOD" editable="1"/>
    <field name="rate_IPO" editable="1"/>
    <field name="rate_PDO" editable="1"/>
    <field name="rate_SAM" editable="1"/>
    <field name="rate_SOI" editable="1"/>
    <field name="rate_tide" editable="1"/>
    <field name="rate_time" editable="1"/>
    <field name="sig_IOD" editable="1"/>
    <field name="sig_IPO" editable="1"/>
    <field name="sig_PDO" editable="1"/>
    <field name="sig_SAM" editable="1"/>
    <field name="sig_SOI" editable="1"/>
    <field name="sig_tide" editable="1"/>
    <field name="sig_time" editable="1"/>
    <field name="soi_outl" editable="1"/>
    <field name="soi_rate" editable="1"/>
    <field name="soi_sig" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="1987-01-01" labelOnTop="0"/>
    <field name="1988" labelOnTop="0"/>
    <field name="1988-01-01" labelOnTop="0"/>
    <field name="1989" labelOnTop="0"/>
    <field name="1989-01-01" labelOnTop="0"/>
    <field name="1990" labelOnTop="0"/>
    <field name="1990-01-01" labelOnTop="0"/>
    <field name="1991" labelOnTop="0"/>
    <field name="1991-01-01" labelOnTop="0"/>
    <field name="1992" labelOnTop="0"/>
    <field name="1992-01-01" labelOnTop="0"/>
    <field name="1993" labelOnTop="0"/>
    <field name="1993-01-01" labelOnTop="0"/>
    <field name="1994" labelOnTop="0"/>
    <field name="1994-01-01" labelOnTop="0"/>
    <field name="1995" labelOnTop="0"/>
    <field name="1995-01-01" labelOnTop="0"/>
    <field name="1996" labelOnTop="0"/>
    <field name="1996-01-01" labelOnTop="0"/>
    <field name="1997" labelOnTop="0"/>
    <field name="1997-01-01" labelOnTop="0"/>
    <field name="1998" labelOnTop="0"/>
    <field name="1998-01-01" labelOnTop="0"/>
    <field name="1999" labelOnTop="0"/>
    <field name="1999-01-01" labelOnTop="0"/>
    <field name="2000" labelOnTop="0"/>
    <field name="2000-01-01" labelOnTop="0"/>
    <field name="2001" labelOnTop="0"/>
    <field name="2001-01-01" labelOnTop="0"/>
    <field name="2002" labelOnTop="0"/>
    <field name="2002-01-01" labelOnTop="0"/>
    <field name="2003" labelOnTop="0"/>
    <field name="2003-01-01" labelOnTop="0"/>
    <field name="2004" labelOnTop="0"/>
    <field name="2004-01-01" labelOnTop="0"/>
    <field name="2005" labelOnTop="0"/>
    <field name="2005-01-01" labelOnTop="0"/>
    <field name="2006" labelOnTop="0"/>
    <field name="2006-01-01" labelOnTop="0"/>
    <field name="2007" labelOnTop="0"/>
    <field name="2007-01-01" labelOnTop="0"/>
    <field name="2008" labelOnTop="0"/>
    <field name="2008-01-01" labelOnTop="0"/>
    <field name="2009" labelOnTop="0"/>
    <field name="2009-01-01" labelOnTop="0"/>
    <field name="2010" labelOnTop="0"/>
    <field name="2010-01-01" labelOnTop="0"/>
    <field name="2011" labelOnTop="0"/>
    <field name="2011-01-01" labelOnTop="0"/>
    <field name="2012" labelOnTop="0"/>
    <field name="2012-01-01" labelOnTop="0"/>
    <field name="2013" labelOnTop="0"/>
    <field name="2013-01-01" labelOnTop="0"/>
    <field name="2014" labelOnTop="0"/>
    <field name="2014-01-01" labelOnTop="0"/>
    <field name="2015" labelOnTop="0"/>
    <field name="2015-01-01" labelOnTop="0"/>
    <field name="2016" labelOnTop="0"/>
    <field name="2016-01-01" labelOnTop="0"/>
    <field name="2017" labelOnTop="0"/>
    <field name="2017-01-01" labelOnTop="0"/>
    <field name="2018" labelOnTop="0"/>
    <field name="2018-01-01" labelOnTop="0"/>
    <field name="breakpoints" labelOnTop="0"/>
    <field name="eln_outl" labelOnTop="0"/>
    <field name="eln_rate" labelOnTop="0"/>
    <field name="eln_sig" labelOnTop="0"/>
    <field name="incpt_IOD" labelOnTop="0"/>
    <field name="incpt_IPO" labelOnTop="0"/>
    <field name="incpt_PDO" labelOnTop="0"/>
    <field name="incpt_SAM" labelOnTop="0"/>
    <field name="incpt_SOI" labelOnTop="0"/>
    <field name="incpt_tide" labelOnTop="0"/>
    <field name="incpt_time" labelOnTop="0"/>
    <field name="lan_outl" labelOnTop="0"/>
    <field name="lan_rate" labelOnTop="0"/>
    <field name="lan_sig" labelOnTop="0"/>
    <field name="mov_outl" labelOnTop="0"/>
    <field name="mov_rate" labelOnTop="0"/>
    <field name="mov_sig" labelOnTop="0"/>
    <field name="move_abs" labelOnTop="0"/>
    <field name="neg_outl" labelOnTop="0"/>
    <field name="neg_rate" labelOnTop="0"/>
    <field name="neg_sig" labelOnTop="0"/>
    <field name="orig_ogc_fid" labelOnTop="0"/>
    <field name="outl_IOD" labelOnTop="0"/>
    <field name="outl_IPO" labelOnTop="0"/>
    <field name="outl_PDO" labelOnTop="0"/>
    <field name="outl_SAM" labelOnTop="0"/>
    <field name="outl_SOI" labelOnTop="0"/>
    <field name="outl_tide" labelOnTop="0"/>
    <field name="outl_time" labelOnTop="0"/>
    <field name="pos_outl" labelOnTop="0"/>
    <field name="pos_rate" labelOnTop="0"/>
    <field name="pos_sig" labelOnTop="0"/>
    <field name="rate_IOD" labelOnTop="0"/>
    <field name="rate_IPO" labelOnTop="0"/>
    <field name="rate_PDO" labelOnTop="0"/>
    <field name="rate_SAM" labelOnTop="0"/>
    <field name="rate_SOI" labelOnTop="0"/>
    <field name="rate_tide" labelOnTop="0"/>
    <field name="rate_time" labelOnTop="0"/>
    <field name="sig_IOD" labelOnTop="0"/>
    <field name="sig_IPO" labelOnTop="0"/>
    <field name="sig_PDO" labelOnTop="0"/>
    <field name="sig_SAM" labelOnTop="0"/>
    <field name="sig_SOI" labelOnTop="0"/>
    <field name="sig_tide" labelOnTop="0"/>
    <field name="sig_time" labelOnTop="0"/>
    <field name="soi_outl" labelOnTop="0"/>
    <field name="soi_rate" labelOnTop="0"/>
    <field name="soi_sig" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>1987-01-01</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
