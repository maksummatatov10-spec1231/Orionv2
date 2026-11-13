package industrialcraft {
 import assets.Images;
 import flash.display.BitmapData;
 import flash.geom.Rectangle;
 import flash.utils.Dictionary;
 import orion.worlds.Block;
 import orion.worlds.Item;
 import orion.worlds.ItemStack;
 import orion.worlds.Recipe;
 import orion.worlds.Ingredient;
 import orion.graphics.TextureAtlas;
 public final class ContentRegistry {
  public static const PROBE_ID:int=1242;
  public static const RUBBER_ID:int=1243;
  public static var RUBBER:Item;
  public static const PROBE_BLOCK_LOCAL_ID:int=239;
  public static const PROBE_BLOCK_ITEM_ID:int=495;
  public static var PROBE:Item;
  public static var PROBE_BLOCK:Block;
  public static var PROBE_BLOCK_ITEM:ICBlockItem;
  private static var installed:Boolean=false;
  public static function install():void {
   if(installed)return;
   if(Item.ITEMS[RUBBER_ID]!=null || Item.ITEMS[PROBE_ID]!=null || Block.BLOCKS[PROBE_BLOCK_LOCAL_ID]!=null || Item.ITEMS[PROBE_BLOCK_ITEM_ID]!=null)
    throw new Error("IC: конфликт ID этапа 0");
   var itemsAtlas:TextureAtlas=Context.atlases.getAtlas("items");
   var tilesAtlas:TextureAtlas=Context.atlases.getAtlas("tiles");
   if(itemsAtlas.textures["item_"+RUBBER_ID]==null || itemsAtlas.textures["item_"+PROBE_ID]==null || itemsAtlas.textures["item_"+PROBE_BLOCK_ITEM_ID]==null || tilesAtlas.textures["block_"+PROBE_BLOCK_LOCAL_ID]==null)
    throw new Error("IC: отсутствуют регионы атласа этапа 0");
   RUBBER=new Item(RUBBER_ID);
   RUBBER.name="Резина";
   RUBBER.description="Материал из древесной смолы. Основа будущей изоляции проводов.";
   RUBBER.maxStackSize=50;
   Images.ITEMS[RUBBER_ID]=ICAssets.rubberIcon();
   var rubberRecipe:Recipe=new Recipe(Recipe.DECORS_CATEGORY,Recipe.WORKBENCH_UTILITY);
   rubberRecipe.craftedItem=new ItemStack(RUBBER,0,1);
   rubberRecipe.ingredients=new <Ingredient>[new Ingredient(Item.RESIN,2)];
   PROBE=new Item(PROBE_ID);
   PROBE.name="Калибровочный модуль";
   PROBE.description="Технический предмет этапа 0. Проверяет реестр, иконку и сохранение.";
   PROBE.maxStackSize=50;
   PROBE_BLOCK=new ICBlock(PROBE_BLOCK_LOCAL_ID);
   PROBE_BLOCK_ITEM=new ICBlockItem(PROBE_BLOCK_LOCAL_ID,PROBE_BLOCK);
   PROBE_BLOCK_ITEM.name="Калибровочный станок";
   PROBE_BLOCK_ITEM.description="Смола → калибровочный модуль за 5 секунд. Технический механизм этапа 0.";
   Images.ITEMS[PROBE_ID]=ICAssets.probeIcon();
   Images.ITEMS[PROBE_BLOCK_ITEM_ID]=ICAssets.probeIcon();
   var recipe:Recipe=new Recipe(Recipe.DECORS_CATEGORY,Recipe.WORKBENCH_UTILITY);
   recipe.craftedItem=new ItemStack(PROBE_BLOCK_ITEM,0,1);
   recipe.ingredients=new <Ingredient>[new Ingredient(Item.COBBLESTONE,4),new Ingredient(Item.RESIN,1)];
   installed=true;
   trace("IC_RUBBER_READY id="+RUBBER.id+" resin="+Item.RESIN.id+" recipeResin=2");
   trace("IC_CONTENT_READY probe="+PROBE.id+" block="+PROBE_BLOCK.id+" blockItem="+PROBE_BLOCK_ITEM.id);
  }
 }
}
