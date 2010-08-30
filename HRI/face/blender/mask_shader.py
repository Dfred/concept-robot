#added by Dasari Pavan Kumar .. dasaripavan@gmail.com
#under GPL

import GameLogic
object_list = GameLogic.getCurrentScene().getObjectList();

VertexShader = """

varying vec3 normal;
varying vec3 lightDir;
varying vec3 halfVector;
varying vec4 color;
uniform sampler2D testTexture;
void main()
{
        gl_TexCoord[0] = gl_MultiTexCoord0 ;
        normal     = normalize ( gl_NormalMatrix * gl_Normal      ) ;
        lightDir   = normalize ( gl_LightSource[0].position.xyz   ) ;
        halfVector = normalize ( gl_LightSource[0].halfVector.xyz ) ;
        
        vec3 tex = texture2D(testTexture, vec2(gl_MultiTexCoord0)).rgb;//corresponding texture values
        color = gl_Color;//initial color set to opengl color assigned to that vertex
        
        vec4 WC = gl_Vertex;
        
		//------- center of projection along Y is varied according to vertex 'y' coordinate
		float CPy;
		if(WC.y>0.1)
		{
			//above posivite y axis, so push center of projection down
			CPy = WC.y-0.3;
		}
		else if(WC.y<-0.1)
		{
			//vice versa .. different values to observe difference in stretching
			CPy = WC.y+0.1;
		}
		else
		{
			CPy = WC.y;//unchanged
		}
		//----------------------------------------------------------------------------------//
		//a,b,c are the radii of 3D superquadric onto which the mesh is projected with origin as center
		//cx,cy,cz are the coordinates for the center of projection
				
        float a = 1.5, b = 0.5, c = 1.8, cx = 0.0, cy = CPy, cz = 0.2*(1.0-tex.x);//0.0;
//				if(tex.x>0.95 && tex.y>0.95 && tex.z>0.95)//assuming a grey scale map
		if(tex.x>0.05)
        {
			//assuming a superquadrics of order 3... hence solving for cube root                
			float P = abs(WC.x-cx);
			float Q = abs(WC.y-cy);
			float R = abs(WC.z-cz);
								
			float A = ((P*P*P)/(a*a*a)) + ((Q*Q*Q)/(b*b*b)) + ((R*R*R)/(c*c*c));
			float B = 3.0*(((P*P*cx)/(a*a*a)) + ((Q*Q*cy)/(b*b*b)) + ((R*R*cz)/(c*c*c)));
			float C = 3.0*(((P*cx*cx)/(a*a*a)) + ((Q*cy*cy)/(b*b*b)) + ((R*cz*cz)/(c*c*c)));
			float D = ((cx*cx*cx)/(a*a*a)) + ((cy*cy*cy)/(b*b*b)) + ((cz*cz*cz)/(c*c*c)) - 1.0;
		
			float M = (C/A) - ((B*B)/(3.0*A*A));
			float N = ((B*C)/(3.0*A*A)) - ((2.0*B*B*B)/(27.0*A*A*A)) - (D/A);
															
			float r1 = pow( ( N + sqrt( (N*N) + (4.0*M*M*M)/27.0 ) )/2.0, 1.0/3.0);
			float r2 = pow( ( -N + sqrt( (N*N) + (4.0*M*M*M)/27.0 ) )/2.0 , 1.0/3.0);

			if(( -N + sqrt( (N*N) + (4.0*M*M*M)/27.0 ) )<0.0 && ( -N + sqrt( (N*N) + (4.0*M*M*M)/27.0 ) )>-0.001)
			{
				//this check had to be done because of floating point errors!	
				r2 = 0.0;
			}
								
			float tOne = r1 - r2 - (B/(3.0*A));
			tOne = 1+ (tOne-1)*tex.x;
			WC = vec4(cx + (WC.x-cx)*tOne, cy + (WC.y-cy)*tOne, -0.1 + cz + (WC.z-cz)*tOne, WC.w);
			normal = normalize( vec3(WC.x-cx,WC.y-cy,WC.z-cz) );
			//---------------------------------------------------------------------//

			//assuming a 3D ellipsoid .. this is of order 2..
			//float A = (((WC.x-cx)*(WC.x-cx))/(a*a)) + (((WC.y-cy)*(WC.y-cy))/(b*b)) + (((WC.z-cz)*(WC.z-cz))/(c*c));
			//float B = (((WC.x-cx)*cx)/(a*a)) + (((WC.y-cy)*cy)/(b*b)) + (((WC.z-cz)*cz)/(c*c));
			//float C = ((cx*cx)/(a*a)) + ((cy*cy)/(b*b)) + ((cz*cz)/(c*c)) - 1.0;
								
			//float tOne = (-B + sqrt((B*B) - (4.0*A*C)))/(2.0*A);
			//float tTwo = (-B - sqrt((B*B) - (4.0*A*C)))/(2.0*A);
			//WC = vec4(cx + (WC.x-cx)*tOne, cy + (WC.y-cy)*tOne, -0.1 + cz + (WC.z-cz)*tOne, WC.w);
			//normal = normalize( vec3(WC.x-cx,WC.y-cy,WC.z-cz) );
			//----------------------------------------------------------------//
								
			//if(tOne>1.0)
			//{
                //color = vec4(0.0, 1.0, 0.0, 1.0);
            //}       
        }
        
        gl_Position = gl_ProjectionMatrix*gl_ModelViewMatrix*WC;
        
}
"""

FragmentShader = """

//uniform sampler2D mytexture ;
varying vec3 normal, lightDir, halfVector ;
varying vec4 color;

void main()
{
        vec3  dl = gl_LightSource[0].diffuse .rgb * gl_FrontMaterial.diffuse.rgb ;
        vec3  al = gl_LightSource[0].ambient .rgb * gl_FrontMaterial.ambient.rgb +
                                               gl_FrontMaterial.emission.rgb ;
        vec3  sl = gl_LightSource[0].specular.rgb * gl_FrontMaterial.specular.rgb ;

        //vec3  tx = texture2D ( mytexture, vec2(gl_TexCoord[0]) ).rgb ;

        float sh = gl_FrontMaterial.shininess ;
        vec3 n = normalize ( normal ) ;
        vec3 d = color.xyz * ( dl * max ( dot ( n, lightDir                 ), 0.0 ) + al ) ;
        vec3 s = sl *  pow ( max ( dot ( n, normalize ( halfVector ) ), 0.0 ), sh ) ;
         
        gl_FragColor = vec4 ( min ( d + s, 1.0) , 1.0 ) ;//vec4(tx,color.a);
}
"""

print object_list;
shader_objs = [ object_list['OBbody'] ];
print shader_objs;
for obj in shader_objs:
	mesh = obj.getMesh();
	print mesh;
	print mesh.materials;
	for mat in mesh.materials:
		print "hello mat: ", mat;
#		if not hasattr(mat,"getMaterialIndex"):
#			break;
		
#		mat_index = mat.getMaterialIndex();
#		print "mat_index: ",mat_index,"  ", mat;
        #use shader only for skin!
		if mat:
			shader = mat.getShader();
			if not shader.isValid():
				print "setting shader!... ", dir(shader);
				shader.setSource(VertexShader,FragmentShader,1);
				shader.setNumberOfPasses(1);
				#print shader.getVertexProg();
				#shader.setSampler('mytexture',0);
				shader.setSampler('testTexture',0);
