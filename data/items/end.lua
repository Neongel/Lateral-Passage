-- 终点物品功能脚本
-- 当玩家触碰终点时触发通关

function on_touch(player, item, map_data)
    -- 设置通关状态
    player.won = true
    return true
end

function on_update(item, dt)
    -- 终点不需要每帧更新
end

function on_draw(item, screen, x, y, tile_size)
    -- 使用纹理绘制，返回false让系统默认绘制
    return false
end
