package industrialcraft {
 import flash.display.BitmapData;
 import flash.geom.Rectangle;
 public final class ICAssets {
  public static function probeIcon():BitmapData {
   var b:BitmapData=new BitmapData(32,32,true,0);
   var dark:uint=0xff2b1d18, wood:uint=0xff84532d, light:uint=0xffb87c41, brass:uint=0xffc59146, hi:uint=0xffefbe63;
   var teal:uint=0xff418b84, glass:uint=0xff7ecdb8, black:uint=0xff1b1f1e, shade:uint=0xff533523;
   b.fillRect(new Rectangle(5,7,22,21),dark);b.fillRect(new Rectangle(7,6,18,3),dark);
   b.fillRect(new Rectangle(7,9,18,17),wood);b.fillRect(new Rectangle(9,10,14,14),shade);
   b.fillRect(new Rectangle(10,11,12,11),brass);b.fillRect(new Rectangle(12,12,8,8),black);
   b.fillRect(new Rectangle(13,13,6,6),teal);b.fillRect(new Rectangle(13,13,4,2),glass);
   b.fillRect(new Rectangle(8,9,16,2),light);b.fillRect(new Rectangle(8,24,16,2),shade);
   b.fillRect(new Rectangle(8,11,1,1),hi);b.fillRect(new Rectangle(22,11,1,1),hi);b.fillRect(new Rectangle(8,22,1,1),hi);b.fillRect(new Rectangle(22,22,1,1),hi);
   b.fillRect(new Rectangle(11,4,3,3),dark);b.fillRect(new Rectangle(18,4,3,3),dark);b.fillRect(new Rectangle(12,3,1,3),brass);b.fillRect(new Rectangle(19,3,1,3),brass);
   return b;
  }
 }
}
