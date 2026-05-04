-- 门功能脚本
-- 当玩家距离门小于等于1格时，点击可切换开关
-- 门关闭时阻挡玩家，打开时可通过

function on_touch(player, item, map_data)
    -- 门不自动触发，通过点击触发
    return false
end

function on_update(item, dt)
    -- 门不需要每帧更新
end

function on_draw(item, screen, x, y, tile_size)
    -- 使用纹理绘制，返回false让系统默认绘制
    return false
end
