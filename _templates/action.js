/* VRO ACTION START */
/* id:{{ action.id }} */
/**
 * {% if description %}{{ description }}
 * 
 * {% endif %}@method {{ action.name }} 
 *{% for p in action.params %}
 * @param {% raw %}{{% endraw %}{{ p.type }}{% raw %}}{% endraw %} {{ p.name }}{% if p.desc %} {{ p.desc }}{% endif %}{% endfor %}
 * 
 * @return {% raw %}{{% endraw %}{{ action.js_result }}{% raw %}}{% endraw %}
 */
function {{ action.name }} () {
    {{ script }}
};
/* VRO ACTION END */



