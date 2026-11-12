package {
  import flash.display.Sprite;
  import flash.utils.getDefinitionByName;
  import flash.utils.setTimeout;
  public class VerifyBootstrap extends Sprite {
    public static var _started:Boolean = start();
    private static var tries:int = 0;
    public static function start():Boolean { setTimeout(tick, 2000); return true; }
    private static function tick():void {
      tries++;
      try {
        var C:* = getDefinitionByName("Context");
        var game:* = C.game;
        if (game && game.inventory && game.player && C.world && C.world.tilesX > 0 && game.player.center.x > 0 && game.player.center.y > 0) {
          var ItemC:* = getDefinitionByName("orion.worlds.Item");
          var StackC:* = getDefinitionByName("orion.worlds.ItemStack");
          var BlockC:* = getDefinitionByName("orion.worlds.Block");
          var WallC:* = getDefinitionByName("orion.worlds.Wall");
          var inv:* = game.inventory;
          var armorIds:Array = [1208, 1209, 1215];
          for (var i:int = 0; i < 3; i++) {
            var st:* = new StackC(ItemC.ITEMS[armorIds[i]], 0, 1);
            st.durability = 30; inv.armors[i] = st;
          }
          var dropIds:Array = [1024, 1194, 1025, 1026, 1027, 1028];
          for (i = 0; i < dropIds.length; i++) {
            inv.items[i] = new StackC(ItemC.ITEMS[dropIds[i]], 0, 99);
          }
          inv.items[6] = new StackC(ItemC.ITEMS[259], 0, 99);
          var w:* = C.world; var p:* = game.player;
          var tx:int = int(p.center.x / 32); var ty:int = int(p.center.y / 32);
          var gy:int = ty;
          for (var yy:int = ty; yy < ty + 8; yy++) {
            var t:* = w.tiles[tx + yy * w.tilesX];
            if (t.blockId != 0 && BlockC.BLOCKS[t.blockId].hard) { gy = yy; break; }
          }
          var x0:int = tx - 8; var rowY:int = gy - 1;
          var ids:Array = [4, 5, 167, 6, 7, 8, 9, 4];
          for (i = 0; i < ids.length; i++) {
            var x:int = x0 + i;
            if (x >= 0 && x < w.tilesX && rowY >= 0 && rowY < w.tilesY) {
              w.setBlock(x, rowY, BlockC.BLOCKS[ids[i]]);
            }
          }
          var wallIds:Array = [4, 5, 6];
          for (var wx:int = 0; wx < 3; wx++) {
            for (var wy:int = -3; wy <= -1; wy++) {
              var xx:int = x0 + 10 + wx; var yy2:int = rowY + wy;
              if (xx >= 0 && xx < w.tilesX && yy2 >= 0 && yy2 < w.tilesY) {
                w.setWall(xx, yy2, WallC.WALLS[wallIds[wx]]);
              }
            }
          }
          trace("V05_VERIFY_READY tx=" + tx + " gy=" + gy + " rowY=" + rowY);
          return;
        }
      } catch (e:Error) {
        trace("V05_VERIFY_ERR " + e.toString());
      }
      if (tries < 200) setTimeout(tick, 500);
    }
  }
}
